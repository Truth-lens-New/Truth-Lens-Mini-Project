import 'package:flutter/material.dart';
import '../models/storage_category.dart';
import '../services/storage_scan_service.dart';
import '../widgets/category_card.dart';
import '../models/storage_stats.dart';

/// Screen listing all storage categories with drill-down support.
class CategoriesScreen extends StatefulWidget {
  final StorageScanService scanService;

  const CategoriesScreen({super.key, required this.scanService});

  @override
  State<CategoriesScreen> createState() => _CategoriesScreenState();
}

class _CategoriesScreenState extends State<CategoriesScreen> {
  List<StorageCategory> _categories = [];
  StorageStats? _stats;
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
      final cats = await widget.scanService.getCategoryBreakdown();
      final stats = await widget.scanService.getStorageStats();
      if (mounted) {
        setState(() {
          _categories = cats
            ..sort((a, b) => b.totalBytes.compareTo(a.totalBytes));
          _stats = stats;
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
        title: const Text('Categories'),
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
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: _categories
                        .map(
                          (c) => Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: CategoryCard(
                              category: c,
                              totalStorageBytes: _stats?.totalBytes ?? 0,
                            ),
                          ),
                        )
                        .toList(),
                  ),
                ),
    );
  }
}
