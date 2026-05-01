package com.example.storage_analyzer

import android.app.AppOpsManager
import android.app.usage.StorageStatsManager
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.database.Cursor
import android.net.Uri
import android.os.StatFs
import android.os.storage.StorageManager
import android.provider.MediaStore
import io.flutter.plugin.common.BinaryMessenger
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.security.MessageDigest
import java.util.UUID

/**
 * Native plugin that backs the Flutter StorageScanService interface.
 *
 * Channel: com.example.storage_analyzer/scan
 *
 * Supported methods:
 *   getStorageStats        → Map<String, Long>
 *   getCategoryBreakdown   → List<Map>
 *   getLargeFiles          → List<Map>  (args: limit: Int)
 *   getDuplicates          → List<Map>  (args: deepScan: Boolean)
 *   getAppStorageInfo      → List<Map>
 *   deleteFile             → Map<String, Any>  (args: path: String)
 */
class StorageScanPlugin(private val context: Context) : MethodChannel.MethodCallHandler {

    companion object {
        private const val CHANNEL = "com.example.storage_analyzer/scan"

        // Document extensions scanned via file-system walk (SAF unavailable for simple paths).
        private val DOC_EXTENSIONS = setOf(
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
            "txt", "csv", "zip", "rar", "7z", "tar", "gz"
        )

        fun register(messenger: BinaryMessenger, context: Context) {
            val channel = MethodChannel(messenger, CHANNEL)
            channel.setMethodCallHandler(StorageScanPlugin(context))
        }
    }

    // ── Method dispatch ──────────────────────────────────────────────────────

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        try {
            when (call.method) {
                "getStorageStats"      -> result.success(getStorageStats())
                "getCategoryBreakdown" -> result.success(getCategoryBreakdown())
                "getLargeFiles"        -> {
                    val limit = call.argument<Int>("limit") ?: 50
                    result.success(getLargeFiles(limit))
                }
                "getDuplicates"        -> {
                    val deepScan = call.argument<Boolean>("deepScan") ?: false
                    result.success(getDuplicates(deepScan))
                }
                "getAppStorageInfo"    -> result.success(getAppStorageInfo())
                "deleteFile"           -> {
                    val path = call.argument<String>("path") ?: ""
                    result.success(deleteFile(path))
                }
                else -> result.notImplemented()
            }
        } catch (e: SecurityException) {
            result.error("PERMISSION_DENIED", e.message, null)
        } catch (e: Exception) {
            result.error("SCAN_ERROR", e.message, null)
        }
    }

    // ── Storage stats ────────────────────────────────────────────────────────

    private fun getStorageStats(): Map<String, Long> {
        val path = context.filesDir
        val stat = StatFs(path.absolutePath)
        val blockSize = stat.blockSizeLong
        val total     = stat.blockCountLong * blockSize
        val available = stat.availableBlocksLong * blockSize
        return mapOf(
            "totalBytes"     to total,
            "availableBytes" to available
        )
    }

    // ── Category breakdown ───────────────────────────────────────────────────

    private fun getCategoryBreakdown(): List<Map<String, Any>> {
        val categories = mutableListOf<Map<String, Any>>()

        categories.add(queryCategoryFromMediaStore("images",
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Images.Media.SIZE))

        categories.add(queryCategoryFromMediaStore("videos",
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Video.Media.SIZE))

        categories.add(queryCategoryFromMediaStore("audio",
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Audio.Media.SIZE))

        categories.add(queryDocuments())

        categories.add(queryAppsCategory())

        categories.add(queryCacheCategory())

        return categories
    }

    private fun queryCategoryFromMediaStore(
        type: String,
        uri: Uri,
        sizeColumn: String
    ): Map<String, Any> {
        var totalBytes = 0L
        var fileCount  = 0

        val projection = arrayOf(sizeColumn)
        val cursor: Cursor? = context.contentResolver.query(
            uri, projection, null, null, "$sizeColumn DESC"
        )
        cursor?.use {
            val sizeIdx = it.getColumnIndex(sizeColumn)
            while (it.moveToNext()) {
                if (sizeIdx >= 0) totalBytes += it.getLong(sizeIdx)
                fileCount++
            }
        }

        return mapOf(
            "type"       to type,
            "totalBytes" to totalBytes,
            "fileCount"  to fileCount
        )
    }

    private fun queryDocuments(): Map<String, Any> {
        var totalBytes = 0L
        var fileCount  = 0

        // MediaStore.Files is available on API 28+ without additional permissions.
        val uri = MediaStore.Files.getContentUri("external")
        val projection = arrayOf(
            MediaStore.Files.FileColumns.SIZE,
            MediaStore.Files.FileColumns.MIME_TYPE
        )
        val docMimeTypes = listOf(
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed"
        )
        val placeholders = docMimeTypes.joinToString(",") { "?" }
        val selection = "${MediaStore.Files.FileColumns.MIME_TYPE} IN ($placeholders)"
        val selArgs  = docMimeTypes.toTypedArray()

        val cursor: Cursor? = context.contentResolver.query(
            uri, projection, selection, selArgs,
            "${MediaStore.Files.FileColumns.SIZE} DESC"
        )
        cursor?.use {
            val sizeIdx = it.getColumnIndex(MediaStore.Files.FileColumns.SIZE)
            while (it.moveToNext()) {
                if (sizeIdx >= 0) totalBytes += it.getLong(sizeIdx)
                fileCount++
            }
        }

        return mapOf(
            "type"       to "documents",
            "totalBytes" to totalBytes,
            "fileCount"  to fileCount
        )
    }

    private fun queryAppsCategory(): Map<String, Any> {
        val pm = context.packageManager
        val apps = pm.getInstalledApplications(PackageManager.GET_META_DATA)
        var totalBytes = 0L
        for (app in apps) {
            try {
                val file = File(app.sourceDir)
                if (file.exists()) totalBytes += file.length()
            } catch (_: Exception) { /* skip inaccessible */ }
        }
        return mapOf(
            "type"       to "apps",
            "totalBytes" to totalBytes,
            "fileCount"  to apps.size
        )
    }

    private fun queryCacheCategory(): Map<String, Any> {
        // Only app's own cache is reliably accessible; report with note.
        val cacheDir = context.cacheDir
        val externalCache = context.externalCacheDir
        var totalBytes = dirSize(cacheDir) + (externalCache?.let { dirSize(it) } ?: 0L)
        return mapOf(
            "type"       to "cache",
            "totalBytes" to totalBytes,
            "fileCount"  to 0  // not counting individual cache files
        )
    }

    // ── Large files ──────────────────────────────────────────────────────────

    private fun getLargeFiles(limit: Int): List<Map<String, Any>> {
        val results = mutableListOf<Map<String, Any>>()

        // Query all three media types and merge.
        results.addAll(queryLargeFromUri(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Images.Media.SIZE,
            MediaStore.Images.Media.DATA,
            MediaStore.Images.Media.DISPLAY_NAME,
            MediaStore.Images.Media.DATE_MODIFIED,
            "images",
            limit
        ))
        results.addAll(queryLargeFromUri(
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Video.Media.SIZE,
            MediaStore.Video.Media.DATA,
            MediaStore.Video.Media.DISPLAY_NAME,
            MediaStore.Video.Media.DATE_MODIFIED,
            "videos",
            limit
        ))
        results.addAll(queryLargeFromUri(
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Audio.Media.SIZE,
            MediaStore.Audio.Media.DATA,
            MediaStore.Audio.Media.DISPLAY_NAME,
            MediaStore.Audio.Media.DATE_MODIFIED,
            "audio",
            limit
        ))

        // Documents via MediaStore.Files
        results.addAll(queryLargeDocuments(limit))

        // Sort by size descending and return top `limit` entries.
        return results
            .sortedByDescending { it["sizeBytes"] as Long }
            .take(limit)
    }

    private fun queryLargeFromUri(
        uri: Uri,
        sizeCol: String,
        dataCol: String,
        nameCol: String,
        dateCol: String,
        category: String,
        limit: Int
    ): List<Map<String, Any>> {
        val projection = arrayOf(sizeCol, dataCol, nameCol, dateCol)
        val cursor: Cursor? = context.contentResolver.query(
            uri, projection, null, null, "$sizeCol DESC"
        )
        val items = mutableListOf<Map<String, Any>>()
        cursor?.use {
            val sizeIdx = it.getColumnIndex(sizeCol)
            val dataIdx = it.getColumnIndex(dataCol)
            val nameIdx = it.getColumnIndex(nameCol)
            val dateIdx = it.getColumnIndex(dateCol)
            var count   = 0
            while (it.moveToNext() && count < limit) {
                val sizeBytes = if (sizeIdx >= 0) it.getLong(sizeIdx) else 0L
                if (sizeBytes <= 0) continue
                items.add(mapOf(
                    "path"       to (if (dataIdx >= 0) it.getString(dataIdx) ?: "" else ""),
                    "name"       to (if (nameIdx >= 0) it.getString(nameIdx) ?: "" else ""),
                    "sizeBytes"  to sizeBytes,
                    "modifiedAt" to if (dateIdx >= 0) it.getLong(dateIdx) * 1000L else 0L,
                    "category"   to category
                ))
                count++
            }
        }
        return items
    }

    private fun queryLargeDocuments(limit: Int): List<Map<String, Any>> {
        val uri = MediaStore.Files.getContentUri("external")
        val projection = arrayOf(
            MediaStore.Files.FileColumns.SIZE,
            MediaStore.Files.FileColumns.DATA,
            MediaStore.Files.FileColumns.DISPLAY_NAME,
            MediaStore.Files.FileColumns.DATE_MODIFIED,
            MediaStore.Files.FileColumns.MIME_TYPE
        )
        val docMimeTypes = listOf(
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain",
            "application/zip"
        )
        val placeholders = docMimeTypes.joinToString(",") { "?" }
        val selection = "${MediaStore.Files.FileColumns.MIME_TYPE} IN ($placeholders)"
        val cursor: Cursor? = context.contentResolver.query(
            uri, projection, selection, docMimeTypes.toTypedArray(),
            "${MediaStore.Files.FileColumns.SIZE} DESC"
        )
        val items = mutableListOf<Map<String, Any>>()
        cursor?.use {
            val sizeIdx = it.getColumnIndex(MediaStore.Files.FileColumns.SIZE)
            val dataIdx = it.getColumnIndex(MediaStore.Files.FileColumns.DATA)
            val nameIdx = it.getColumnIndex(MediaStore.Files.FileColumns.DISPLAY_NAME)
            val dateIdx = it.getColumnIndex(MediaStore.Files.FileColumns.DATE_MODIFIED)
            var count   = 0
            while (it.moveToNext() && count < limit) {
                val sizeBytes = if (sizeIdx >= 0) it.getLong(sizeIdx) else 0L
                if (sizeBytes <= 0) continue
                items.add(mapOf(
                    "path"       to (if (dataIdx >= 0) it.getString(dataIdx) ?: "" else ""),
                    "name"       to (if (nameIdx >= 0) it.getString(nameIdx) ?: "" else ""),
                    "sizeBytes"  to sizeBytes,
                    "modifiedAt" to if (dateIdx >= 0) it.getLong(dateIdx) * 1000L else 0L,
                    "category"   to "documents"
                ))
                count++
            }
        }
        return items
    }

    // ── Duplicate finder ─────────────────────────────────────────────────────

    private fun getDuplicates(deepScan: Boolean): List<Map<String, Any>> {
        // Pass 1: collect all files from MediaStore → group by size.
        data class FileEntry(
            val path: String,
            val name: String,
            val sizeBytes: Long,
            val modifiedAt: Long,
            val category: String
        )

        val allFiles = mutableListOf<FileEntry>()
        for ((uri, sizeCol, dataCol, nameCol, dateCol, cat) in listOf(
            MediaStoreQuery(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                MediaStore.Images.Media.SIZE, MediaStore.Images.Media.DATA,
                MediaStore.Images.Media.DISPLAY_NAME, MediaStore.Images.Media.DATE_MODIFIED, "images"),
            MediaStoreQuery(MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
                MediaStore.Video.Media.SIZE, MediaStore.Video.Media.DATA,
                MediaStore.Video.Media.DISPLAY_NAME, MediaStore.Video.Media.DATE_MODIFIED, "videos"),
            MediaStoreQuery(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                MediaStore.Audio.Media.SIZE, MediaStore.Audio.Media.DATA,
                MediaStore.Audio.Media.DISPLAY_NAME, MediaStore.Audio.Media.DATE_MODIFIED, "audio")
        )) {
            val cursor: Cursor? = context.contentResolver.query(
                uri, arrayOf(sizeCol, dataCol, nameCol, dateCol), null, null, null
            )
            cursor?.use {
                val sizeIdx = it.getColumnIndex(sizeCol)
                val dataIdx = it.getColumnIndex(dataCol)
                val nameIdx = it.getColumnIndex(nameCol)
                val dateIdx = it.getColumnIndex(dateCol)
                while (it.moveToNext()) {
                    val sz = if (sizeIdx >= 0) it.getLong(sizeIdx) else 0L
                    if (sz <= 0) continue
                    allFiles.add(FileEntry(
                        path       = if (dataIdx >= 0) it.getString(dataIdx) ?: "" else "",
                        name       = if (nameIdx >= 0) it.getString(nameIdx) ?: "" else "",
                        sizeBytes  = sz,
                        modifiedAt = if (dateIdx >= 0) it.getLong(dateIdx) * 1000L else 0L,
                        category   = cat
                    ))
                }
            }
        }

        // Group by size; keep only groups with 2+ files.
        val bySizeGroups = allFiles
            .groupBy { it.sizeBytes }
            .filter { it.value.size >= 2 }

        if (!deepScan) {
            return bySizeGroups.map { (size, files) ->
                mapOf(
                    "sizeBytes"   to size,
                    "contentHash" to null,
                    "files"       to files.map { f ->
                        mapOf(
                            "path"       to f.path,
                            "name"       to f.name,
                            "sizeBytes"  to f.sizeBytes,
                            "modifiedAt" to f.modifiedAt,
                            "category"   to f.category
                        )
                    }
                )
            }.sortedByDescending { ((it["files"] as List<*>).size - 1) * (it["sizeBytes"] as Long) }
        }

        // Pass 2 (deep scan): compute SHA-256 for each candidate and re-group.
        val result = mutableListOf<Map<String, Any>>()
        for ((size, files) in bySizeGroups) {
            // Map from hash → list of FileEntry
            val byHash = mutableMapOf<String, MutableList<FileEntry>>()
            for (file in files) {
                val hash = computeHash(file.path) ?: continue
                byHash.getOrPut(hash) { mutableListOf() }.add(file)
            }
            for ((hash, hashFiles) in byHash) {
                if (hashFiles.size >= 2) {
                    result.add(mapOf(
                        "sizeBytes"   to size,
                        "contentHash" to hash,
                        "files"       to hashFiles.map { f ->
                            mapOf(
                                "path"       to f.path,
                                "name"       to f.name,
                                "sizeBytes"  to f.sizeBytes,
                                "modifiedAt" to f.modifiedAt,
                                "category"   to f.category
                            )
                        }
                    ))
                }
            }
        }
        return result.sortedByDescending {
            ((it["files"] as List<*>).size - 1) * (it["sizeBytes"] as Long)
        }
    }

    // ── Per-app storage ──────────────────────────────────────────────────────

    private fun getAppStorageInfo(): List<Map<String, Any>> {
        val pm = context.packageManager
        val apps = pm.getInstalledApplications(0)
        val result = mutableListOf<Map<String, Any>>()

        val storageStatsManager: StorageStatsManager? = if (hasUsageStatsPermission()) {
            context.getSystemService(StorageStatsManager::class.java)
        } else null

        val storageManager = context.getSystemService(StorageManager::class.java)
        // Use UUID_DEFAULT (internal storage) if the primary volume UUID is unavailable.
        val storageVolumeUuid: UUID = try {
            storageManager?.primaryStorageVolume?.uuid?.let { UUID.fromString(it) }
                ?: StorageManager.UUID_DEFAULT
        } catch (_: Exception) {
            StorageManager.UUID_DEFAULT
        }

        for (app in apps) {
            val appName = try {
                pm.getApplicationLabel(app).toString()
            } catch (_: Exception) { app.packageName }

            if (storageStatsManager != null) {
                try {
                    val stats = storageStatsManager.queryStatsForPackage(
                        storageVolumeUuid,
                        app.packageName,
                        android.os.Process.myUserHandle()
                    )
                    result.add(mapOf(
                        "packageName" to app.packageName,
                        "appName"     to appName,
                        "appBytes"    to stats.appBytes,
                        "dataBytes"   to stats.dataBytes,
                        "cacheBytes"  to stats.cacheBytes,
                        "isAccurate"  to true
                    ))
                } catch (_: Exception) {
                    result.add(estimatedAppEntry(app, appName, pm))
                }
            } else {
                result.add(estimatedAppEntry(app, appName, pm))
            }
        }

        return result.sortedByDescending {
            val a = it["appBytes"] as Long
            val d = it["dataBytes"] as Long
            val c = it["cacheBytes"] as Long
            a + d + c
        }
    }

    private fun estimatedAppEntry(
        app: ApplicationInfo,
        appName: String,
        pm: PackageManager
    ): Map<String, Any> {
        val apkSize = try { File(app.sourceDir).length() } catch (_: Exception) { 0L }
        return mapOf(
            "packageName" to app.packageName,
            "appName"     to appName,
            "appBytes"    to apkSize,
            "dataBytes"   to 0L,
            "cacheBytes"  to 0L,
            "isAccurate"  to false
        )
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            context.packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    // ── Delete ───────────────────────────────────────────────────────────────

    /**
     * Deletes the file at [path] using MediaStore if possible.
     *
     * Returns a map with keys: success (Boolean), message (String?).
     *
     * Restrictions:
     *  - On Android 10+ (API 29+) only MediaStore-indexed files that this app
     *    owns can be deleted without a RecoverableSecurityException SAF flow.
     *    For simplicity in this scaffold we attempt direct delete and fall back
     *    gracefully rather than launching a full SAF intent.
     *  - Files outside MediaStore return success=false with an explanation.
     */
    private fun deleteFile(path: String): Map<String, Any> {
        if (path.isBlank()) {
            return mapOf("success" to false, "message" to "No path provided.")
        }

        val file = File(path)

        // Attempt MediaStore deletion first (works for owned-media on API 29+).
        val uris = listOf(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
            MediaStore.Files.getContentUri("external")
        )

        for (baseUri in uris) {
            val deleted = context.contentResolver.delete(
                baseUri,
                "${MediaStore.MediaColumns.DATA} = ?",
                arrayOf(path)
            )
            if (deleted > 0) {
                return mapOf("success" to true,
                    "message" to "Deleted via MediaStore.")
            }
        }

        // Fallback: direct file deletion (accessible for app-created files).
        return if (file.exists() && file.delete()) {
            mapOf("success" to true, "message" to "Deleted directly.")
        } else {
            mapOf(
                "success" to false,
                "message" to "Cannot delete: file is protected by Android scoped storage. " +
                    "On Android 11+ only files owned by this app or those in shared " +
                    "MediaStore (images/videos/audio) accessible via SAF can be deleted."
            )
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    /**
     * Computes SHA-256 hex digest for the file at [path].
     * Returns null if file is inaccessible or too large (> 512 MB guard).
     */
    private fun computeHash(path: String): String? {
        if (path.isBlank()) return null
        return try {
            val file = File(path)
            if (!file.exists() || !file.canRead()) return null
            if (file.length() > 512L * 1024 * 1024) return null  // skip huge files

            val digest = MessageDigest.getInstance("SHA-256")
            file.inputStream().use { stream ->
                val buffer = ByteArray(64 * 1024)
                var read: Int
                while (stream.read(buffer).also { read = it } != -1) {
                    digest.update(buffer, 0, read)
                }
            }
            digest.digest().joinToString("") { "%02x".format(it) }
        } catch (_: Exception) {
            null
        }
    }

    private fun dirSize(dir: File): Long {
        if (!dir.exists() || !dir.isDirectory) return 0L
        return dir.walkTopDown()
            .filter { it.isFile }
            .sumOf { it.length() }
    }

    // Simple data class to hold MediaStore query parameters for the duplicate scan loop.
    private data class MediaStoreQuery(
        val uri: Uri,
        val sizeCol: String,
        val dataCol: String,
        val nameCol: String,
        val dateCol: String,
        val category: String
    )
}
