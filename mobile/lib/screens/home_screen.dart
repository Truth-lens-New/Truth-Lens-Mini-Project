import 'package:flutter/material.dart';
import '../models/storage_category.dart';
import '../models/storage_stats.dart';
import '../services/storage_scan_service.dart';
import '../widgets/category_card.dart';
import '../widgets/storage_bar.dart';
import '../utils/format_bytes.dart';

/// Main dashboard screen: shows overall storage usage and category breakdown.
class HomeScreen extends StatefulWidget {
  final StorageScanService scanService;

  const HomeScreen({super.key, required this.scanService});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  StorageStats? _stats;
  List<StorageCategory> _categories = [];
  bool _loading = true;
  String? _error;

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
      final stats = await widget.scanService.getStorageStats();
      final categories = await widget.scanService.getCategoryBreakdown();
      if (mounted) {
        setState(() {
          _stats = stats;
          _categories = categories;
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
        title: const Text('Storage Analyzer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadData,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _ErrorView(message: _error!, onRetry: _loadData)
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    final stats = _stats;
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (stats != null) ...[
            Text(
              'Device Storage',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            StorageBar(
              usedBytes: stats.usedBytes,
              totalBytes: stats.totalBytes,
            ),
            const SizedBox(height: 4),
            Text(
              '${formatBytes(stats.availableBytes)} available of '
              '${formatBytes(stats.totalBytes)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 20),
          ],
          Text(
            'Categories',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          if (_categories.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: Text(
                  'No category data available.\n'
                  'Grant storage permissions and scan again.',
                  textAlign: TextAlign.center,
                ),
              ),
            )
          else
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 1.5,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
              ),
              itemCount: _categories.length,
              itemBuilder: (context, i) => CategoryCard(
                category: _categories[i],
                totalStorageBytes: stats?.totalBytes ?? 0,
              ),
            ),
          const SizedBox(height: 24),
          const _PermissionNote(),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

class _PermissionNote extends StatelessWidget {
  const _PermissionNote();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.secondaryContainer.withOpacity(0.4),
      child: const Padding(
        padding: EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(Icons.info_outline, size: 18),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Some data may be limited on Android 11+ due to scoped '
                'storage restrictions. Per-app stats require '
                'PACKAGE_USAGE_STATS permission.',
                style: TextStyle(fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
