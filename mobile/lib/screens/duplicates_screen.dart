import 'package:flutter/material.dart';
import '../models/duplicate_group.dart';
import '../services/storage_scan_service.dart';
import '../utils/format_bytes.dart';
import '../widgets/file_list_item.dart';

/// Screen showing duplicate file candidates grouped by size (and optionally hash).
class DuplicatesScreen extends StatefulWidget {
  final StorageScanService scanService;

  const DuplicatesScreen({super.key, required this.scanService});

  @override
  State<DuplicatesScreen> createState() => _DuplicatesScreenState();
}

class _DuplicatesScreenState extends State<DuplicatesScreen> {
  List<DuplicateGroup> _groups = [];
  bool _loading = true;
  String? _error;
  bool _deepScan = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData({bool deepScan = false}) async {
    setState(() {
      _loading = true;
      _error = null;
      _deepScan = deepScan;
    });
    try {
      final groups =
          await widget.scanService.getDuplicates(deepScan: deepScan);
      if (mounted) {
        setState(() {
          _groups = groups
            ..sort((a, b) => b.wastedBytes.compareTo(a.wastedBytes));
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

  int get _totalWasted =>
      _groups.fold(0, (sum, g) => sum + g.wastedBytes);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Duplicates'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Fast scan',
            onPressed: () => _loadData(),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : Column(
                  children: [
                    _buildHeader(),
                    Expanded(
                      child: _groups.isEmpty
                          ? const Center(
                              child: Text('No duplicate candidates found.'))
                          : RefreshIndicator(
                              onRefresh: () => _loadData(deepScan: _deepScan),
                              child: ListView.builder(
                                itemCount: _groups.length,
                                itemBuilder: (ctx, i) =>
                                    _GroupTile(group: _groups[i]),
                              ),
                            ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildHeader() {
    return Container(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${_groups.length} group(s) — ${formatBytes(_totalWasted)} wasted',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                Text(
                  _deepScan
                      ? 'Hash-confirmed duplicates'
                      : 'Size-based candidates (enable deep scan to confirm)',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          Switch(
            value: _deepScan,
            onChanged: (v) => _loadData(deepScan: v),
          ),
          const Text('Deep\nscan', style: TextStyle(fontSize: 11)),
        ],
      ),
    );
  }
}

class _GroupTile extends StatelessWidget {
  final DuplicateGroup group;

  const _GroupTile({required this.group});

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      leading: CircleAvatar(
        backgroundColor: Colors.orange.withOpacity(0.15),
        child: const Icon(Icons.copy_outlined, color: Colors.orange),
      ),
      title: Text(
        '${group.files.length} files × ${formatBytes(group.sizeBytes)}',
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
      subtitle: Text(
        '${formatBytes(group.wastedBytes)} wasted'
        '${group.isHashConfirmed ? ' · hash confirmed ✓' : ''}',
        style: TextStyle(
          color: group.isHashConfirmed ? Colors.green : Colors.orange,
        ),
      ),
      children: group.files
          .map((f) => FileListItem(file: f))
          .toList(),
    );
  }
}
