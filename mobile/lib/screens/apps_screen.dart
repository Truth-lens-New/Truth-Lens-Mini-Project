import 'package:flutter/material.dart';
import '../models/app_storage_info.dart';
import '../services/storage_scan_service.dart';
import '../utils/format_bytes.dart';

/// Screen showing per-app storage breakdown.
class AppsScreen extends StatefulWidget {
  final StorageScanService scanService;

  const AppsScreen({super.key, required this.scanService});

  @override
  State<AppsScreen> createState() => _AppsScreenState();
}

class _AppsScreenState extends State<AppsScreen> {
  List<AppStorageInfo> _apps = [];
  bool _loading = true;
  String? _error;
  bool _hasLimitedData = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final apps = await widget.scanService.getAppStorageInfo();
      if (mounted) {
        setState(() {
          _apps = apps..sort((a, b) => b.totalBytes.compareTo(a.totalBytes));
          _hasLimitedData = apps.any((a) => !a.isAccurate);
          _loading = false;
        });
      }
    } on StorageScanException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('App Storage'),
        actions: [
          IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh',
              onPressed: _loadData),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : Column(
                  children: [
                    if (_hasLimitedData) _LimitedBanner(),
                    Expanded(
                      child: _apps.isEmpty
                          ? const Center(
                              child: Text(
                                'No app usage data available.\n'
                                'Grant PACKAGE_USAGE_STATS permission '
                                'to see per-app breakdown.',
                                textAlign: TextAlign.center,
                              ),
                            )
                          : RefreshIndicator(
                              onRefresh: _loadData,
                              child: ListView.separated(
                                itemCount: _apps.length,
                                separatorBuilder: (_, __) =>
                                    const Divider(height: 1),
                                itemBuilder: (ctx, i) =>
                                    _AppTile(app: _apps[i]),
                              ),
                            ),
                    ),
                  ],
                ),
    );
  }
}

class _LimitedBanner extends StatelessWidget {
  const _LimitedBanner();
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.amber.shade100,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: const Row(
        children: [
          Icon(Icons.warning_amber_outlined, size: 18, color: Colors.orange),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              'Some apps show estimated data. Grant PACKAGE_USAGE_STATS '
              'permission in Settings → Apps → Special app access for full accuracy.',
              style: TextStyle(fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}

class _AppTile extends StatelessWidget {
  final AppStorageInfo app;

  const _AppTile({required this.app});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: CircleAvatar(
        backgroundColor:
            Theme.of(context).colorScheme.primaryContainer,
        child: Text(
          app.appName.isNotEmpty ? app.appName[0].toUpperCase() : '?',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onPrimaryContainer,
          ),
        ),
      ),
      title: Row(
        children: [
          Expanded(
            child: Text(
              app.appName.isNotEmpty ? app.appName : app.packageName,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (!app.isAccurate)
            const Tooltip(
              message: 'Estimated — grant PACKAGE_USAGE_STATS for accuracy',
              child: Icon(Icons.info_outline, size: 14, color: Colors.orange),
            ),
        ],
      ),
      subtitle: Text(
        'App: ${formatBytes(app.appBytes)}  '
        'Data: ${formatBytes(app.dataBytes)}  '
        'Cache: ${formatBytes(app.cacheBytes)}',
        style: Theme.of(context).textTheme.bodySmall,
      ),
      trailing: Text(
        formatBytes(app.totalBytes),
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
      isThreeLine: false,
    );
  }
}
