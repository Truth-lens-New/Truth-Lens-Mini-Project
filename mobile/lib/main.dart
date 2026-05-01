import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/categories_screen.dart';
import 'screens/large_files_screen.dart';
import 'screens/duplicates_screen.dart';
import 'screens/apps_screen.dart';
import 'services/method_channel_storage_service.dart';

void main() {
  runApp(const StorageAnalyzerApp());
}

class StorageAnalyzerApp extends StatelessWidget {
  const StorageAnalyzerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Storage Analyzer',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1565C0),
        ),
        useMaterial3: true,
      ),
      home: const _RootNav(),
    );
  }
}

class _RootNav extends StatefulWidget {
  const _RootNav();

  @override
  State<_RootNav> createState() => _RootNavState();
}

class _RootNavState extends State<_RootNav> {
  int _selectedIndex = 0;

  // Single shared service instance — platform channel is reused across tabs.
  final _scanService = MethodChannelStorageService();

  late final List<Widget> _pages;
  late final List<NavigationDestination> _destinations;

  @override
  void initState() {
    super.initState();
    _pages = [
      HomeScreen(scanService: _scanService),
      CategoriesScreen(scanService: _scanService),
      LargeFilesScreen(scanService: _scanService),
      DuplicatesScreen(scanService: _scanService),
      AppsScreen(scanService: _scanService),
    ];
    _destinations = const [
      NavigationDestination(
        icon: Icon(Icons.dashboard_outlined),
        selectedIcon: Icon(Icons.dashboard),
        label: 'Dashboard',
      ),
      NavigationDestination(
        icon: Icon(Icons.category_outlined),
        selectedIcon: Icon(Icons.category),
        label: 'Categories',
      ),
      NavigationDestination(
        icon: Icon(Icons.folder_open_outlined),
        selectedIcon: Icon(Icons.folder_open),
        label: 'Large Files',
      ),
      NavigationDestination(
        icon: Icon(Icons.copy_outlined),
        selectedIcon: Icon(Icons.copy),
        label: 'Duplicates',
      ),
      NavigationDestination(
        icon: Icon(Icons.apps_outlined),
        selectedIcon: Icon(Icons.apps),
        label: 'Apps',
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: _destinations,
        labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
      ),
    );
  }
}
