import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

void main() {
  runApp(SkinCareApp(apiClient: ApiClient(baseUrl: apiBaseUrl)));
}

class SkinCareApp extends StatelessWidget {
  const SkinCareApp({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFF2F7D68))
        .copyWith(
          secondary: const Color(0xFFC76B5A),
          tertiary: const Color(0xFF4367A9),
        );
    return MaterialApp(
      title: '肌ケア伴走',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: scheme,
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF7F8F6),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
      ),
      home: HomeScreen(apiClient: apiClient),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _picker = ImagePicker();
  final _budgetController = TextEditingController(text: '2000');
  final _morningMinutesController = TextEditingController(text: '5');
  final _itemsController = TextEditingController(text: '洗顔, 化粧水');
  final _concerns = <String>{'乾燥'};

  XFile? _image;
  Uint8List? _imageBytes;
  AnalyzeResponse? _analysis;
  Recommendations? _recommendations;
  bool _loading = false;
  String? _error;
  int _tabIndex = 0;

  static const concerns = ['乾燥', '赤み', '毛穴', '皮脂', 'くすみ', '敏感'];

  @override
  void dispose() {
    _budgetController.dispose();
    _morningMinutesController.dispose();
    _itemsController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(
      source: source,
      imageQuality: 82,
      maxWidth: 1400,
    );
    if (picked == null) {
      return;
    }
    final bytes = await picked.readAsBytes();
    setState(() {
      _image = picked;
      _imageBytes = bytes;
      _error = null;
    });
  }

  Future<void> _runAnalyze() async {
    if (_image == null) {
      setState(() => _error = '先に肌写真を選択してください。');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final questionnaire = QuestionnairePayload(
        concerns: _concerns.toList(),
        budgetYen: int.tryParse(_budgetController.text) ?? 0,
        morningMinutes: int.tryParse(_morningMinutesController.text) ?? 5,
        currentItems: _itemsController.text
            .split(RegExp(r'[,、\n]'))
            .map((item) => item.trim())
            .where((item) => item.isNotEmpty)
            .toList(),
      );
      final analysis = await widget.apiClient.analyze(
        image: _image!,
        questionnaire: questionnaire,
      );
      final recommendations = await widget.apiClient.recommend(
        skinLogId: analysis.skinLogId,
      );
      setState(() {
        _analysis = analysis;
        _recommendations = recommendations;
        _tabIndex = 1;
      });
    } catch (error) {
      setState(() => _error = '診断に失敗しました: $error');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      _AnalyzeForm(
        concerns: concerns,
        selectedConcerns: _concerns,
        budgetController: _budgetController,
        morningMinutesController: _morningMinutesController,
        itemsController: _itemsController,
        imageBytes: _imageBytes,
        imageName: _image?.name,
        loading: _loading,
        error: _error,
        onConcernChanged: (concern, selected) {
          setState(() {
            if (selected) {
              _concerns.add(concern);
            } else {
              _concerns.remove(concern);
            }
          });
        },
        onPickGallery: () => _pickImage(ImageSource.gallery),
        onPickCamera: () => _pickImage(ImageSource.camera),
        onSubmit: _runAnalyze,
      ),
      ResultScreen(
        analysis: _analysis,
        recommendations: _recommendations,
        onNewLog: () => setState(() => _tabIndex = 0),
      ),
      LogsScreen(apiClient: widget.apiClient),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('肌ケア伴走'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: Text(
                'mock対応',
                style: TextStyle(color: Theme.of(context).colorScheme.primary),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(child: pages[_tabIndex]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tabIndex,
        onDestinationSelected: (index) => setState(() => _tabIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.add_a_photo_outlined),
            selectedIcon: Icon(Icons.add_a_photo),
            label: '診断',
          ),
          NavigationDestination(
            icon: Icon(Icons.spa_outlined),
            selectedIcon: Icon(Icons.spa),
            label: '提案',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined),
            selectedIcon: Icon(Icons.history),
            label: 'ログ',
          ),
        ],
      ),
    );
  }
}

class _AnalyzeForm extends StatelessWidget {
  const _AnalyzeForm({
    required this.concerns,
    required this.selectedConcerns,
    required this.budgetController,
    required this.morningMinutesController,
    required this.itemsController,
    required this.imageBytes,
    required this.imageName,
    required this.loading,
    required this.error,
    required this.onConcernChanged,
    required this.onPickGallery,
    required this.onPickCamera,
    required this.onSubmit,
  });

  final List<String> concerns;
  final Set<String> selectedConcerns;
  final TextEditingController budgetController;
  final TextEditingController morningMinutesController;
  final TextEditingController itemsController;
  final Uint8List? imageBytes;
  final String? imageName;
  final bool loading;
  final String? error;
  final void Function(String concern, bool selected) onConcernChanged;
  final VoidCallback onPickGallery;
  final VoidCallback onPickCamera;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _Section(
          title: '肌写真',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AspectRatio(
                aspectRatio: 4 / 3,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.black12),
                  ),
                  child: imageBytes == null
                      ? const Center(
                          child: Icon(Icons.face_retouching_natural, size: 56),
                        )
                      : ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.memory(imageBytes!, fit: BoxFit.cover),
                        ),
                ),
              ),
              const SizedBox(height: 8),
              if (imageName != null)
                Text(
                  imageName!,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton.icon(
                    onPressed: loading ? null : onPickGallery,
                    icon: const Icon(Icons.photo_library_outlined),
                    label: const Text('写真を選ぶ'),
                  ),
                  OutlinedButton.icon(
                    onPressed: loading ? null : onPickCamera,
                    icon: const Icon(Icons.photo_camera_outlined),
                    label: const Text('カメラで撮る'),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _Section(
          title: '問診',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final concern in concerns)
                    FilterChip(
                      label: Text(concern),
                      selected: selectedConcerns.contains(concern),
                      onSelected: (selected) =>
                          onConcernChanged(concern, selected),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              TextField(
                controller: budgetController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '予算（円）',
                  prefixIcon: Icon(Icons.payments_outlined),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: morningMinutesController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '朝のケア時間（分）',
                  prefixIcon: Icon(Icons.timer_outlined),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: itemsController,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: '今使っているアイテム',
                  prefixIcon: Icon(Icons.inventory_2_outlined),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        FilledButton.icon(
          onPressed: loading ? null : onSubmit,
          icon: loading
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.auto_awesome),
          label: Text(loading ? '診断中...' : '診断して提案を見る'),
        ),
      ],
    );
  }
}

class ResultScreen extends StatelessWidget {
  const ResultScreen({
    super.key,
    required this.analysis,
    required this.recommendations,
    required this.onNewLog,
  });

  final AnalyzeResponse? analysis;
  final Recommendations? recommendations;
  final VoidCallback onNewLog;

  @override
  Widget build(BuildContext context) {
    if (analysis == null || recommendations == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: FilledButton.icon(
            onPressed: onNewLog,
            icon: const Icon(Icons.add_a_photo_outlined),
            label: const Text('肌診断をはじめる'),
          ),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _Section(
          title: '診断結果',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(analysis!.analysis.summary),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final concern in analysis!.analysis.detectedConcerns)
                    Chip(label: Text(concern)),
                ],
              ),
              const SizedBox(height: 12),
              for (final entry in analysis!.analysis.metrics.entries)
                _MetricBar(label: entry.key, value: entry.value),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _Section(
          title: '今日の朝ケア',
          child: _StepList(steps: recommendations!.morningCare),
        ),
        const SizedBox(height: 16),
        _Section(
          title: '今日の夜ケア',
          child: _StepList(steps: recommendations!.nightCare),
        ),
        const SizedBox(height: 16),
        _ProductCard(
          title: '買い足すなら1つだけ',
          product: recommendations!.buyOne,
          highlighted: true,
        ),
        const SizedBox(height: 16),
        Text('商品候補', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        for (final product in recommendations!.products)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: _ProductCard(title: product.category, product: product),
          ),
        const SizedBox(height: 8),
        Text(
          recommendations!.disclaimer,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}

class LogsScreen extends StatelessWidget {
  const LogsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<SkinLogItem>>(
      future: apiClient.fetchLogs(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('ログ取得に失敗しました: ${snapshot.error}'));
        }
        final logs = snapshot.data ?? [];
        if (logs.isEmpty) {
          return const Center(child: Text('まだ過去ログはありません。'));
        }
        return RefreshIndicator(
          onRefresh: () async {
            await apiClient.fetchLogs();
          },
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: logs.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final log = logs[index];
              return Card(
                child: ListTile(
                  title: Text(log.summary),
                  subtitle: Text('${log.createdAt}\n${log.concerns.join('、')}'),
                  isThreeLine: true,
                  leading: const Icon(Icons.spa_outlined),
                ),
              );
            },
          ),
        );
      },
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.black12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _MetricBar extends StatelessWidget {
  const _MetricBar({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(width: 64, child: Text(_metricLabel(label))),
          Expanded(
            child: LinearProgressIndicator(
              value: value / 100,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(width: 36, child: Text('$value')),
        ],
      ),
    );
  }
}

class _StepList extends StatelessWidget {
  const _StepList({required this.steps});

  final List<String> steps;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < steps.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(radius: 12, child: Text('${i + 1}')),
                const SizedBox(width: 8),
                Expanded(child: Text(steps[i])),
              ],
            ),
          ),
      ],
    );
  }
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({
    required this.title,
    required this.product,
    this.highlighted = false,
  });

  final String title;
  final ProductCandidate product;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: highlighted ? const Color(0xFFFFF8EA) : null,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 6),
            Text(product.name, style: Theme.of(context).textTheme.titleMedium),
            Text(
              '${product.brand} / ${product.category} / ${product.priceYen}円',
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final reason in product.reasons)
                  Chip(
                    label: Text(reason),
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

String _metricLabel(String key) {
  const labels = {
    'dryness': '乾燥',
    'redness': '赤み',
    'pores': '毛穴',
    'sebum': '皮脂',
    'dullness': 'くすみ',
    'sensitivity': '敏感',
  };
  return labels[key] ?? key;
}

class ApiClient {
  ApiClient({required this.baseUrl});

  final String baseUrl;

  Future<AnalyzeResponse> analyze({
    required XFile image,
    required QuestionnairePayload questionnaire,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/skin/analyze'),
    );
    request.fields['questionnaire'] = jsonEncode(questionnaire.toJson());
    request.files.add(
      http.MultipartFile.fromBytes(
        'image',
        await image.readAsBytes(),
        filename: image.name.isEmpty ? 'face.jpg' : image.name,
      ),
    );
    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);
    _throwIfFailed(response);
    return AnalyzeResponse.fromJson(jsonDecode(response.body));
  }

  Future<Recommendations> recommend({required String skinLogId}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/recommendations'),
      headers: {'content-type': 'application/json'},
      body: jsonEncode({'skin_log_id': skinLogId}),
    );
    _throwIfFailed(response);
    return Recommendations.fromJson(jsonDecode(response.body));
  }

  Future<List<SkinLogItem>> fetchLogs() async {
    final response = await http.get(Uri.parse('$baseUrl/api/skin-logs'));
    _throwIfFailed(response);
    final decoded = jsonDecode(response.body) as List<dynamic>;
    return decoded.map((item) => SkinLogItem.fromJson(item)).toList();
  }

  void _throwIfFailed(http.Response response) {
    if (response.statusCode >= 400) {
      throw Exception('${response.statusCode}: ${response.body}');
    }
  }
}

class QuestionnairePayload {
  const QuestionnairePayload({
    required this.concerns,
    required this.budgetYen,
    required this.morningMinutes,
    required this.currentItems,
  });

  final List<String> concerns;
  final int budgetYen;
  final int morningMinutes;
  final List<String> currentItems;

  Map<String, dynamic> toJson() => {
    'concerns': concerns,
    'budget_yen': budgetYen,
    'morning_minutes': morningMinutes,
    'current_items': currentItems,
  };
}

class AnalyzeResponse {
  const AnalyzeResponse({required this.skinLogId, required this.analysis});

  final String skinLogId;
  final SkinAnalysis analysis;

  factory AnalyzeResponse.fromJson(Map<String, dynamic> json) {
    return AnalyzeResponse(
      skinLogId: json['skin_log_id'] as String,
      analysis: SkinAnalysis.fromJson(json['analysis'] as Map<String, dynamic>),
    );
  }
}

class SkinAnalysis {
  const SkinAnalysis({
    required this.summary,
    required this.metrics,
    required this.detectedConcerns,
  });

  final String summary;
  final Map<String, int> metrics;
  final List<String> detectedConcerns;

  factory SkinAnalysis.fromJson(Map<String, dynamic> json) {
    final metricsJson = json['metrics'] as Map<String, dynamic>;
    return SkinAnalysis(
      summary: json['summary'] as String,
      metrics: metricsJson.map((key, value) => MapEntry(key, value as int)),
      detectedConcerns: List<String>.from(
        json['detected_concerns'] as List<dynamic>,
      ),
    );
  }
}

class Recommendations {
  const Recommendations({
    required this.carePolicy,
    required this.morningCare,
    required this.nightCare,
    required this.buyOne,
    required this.products,
    required this.disclaimer,
  });

  final String carePolicy;
  final List<String> morningCare;
  final List<String> nightCare;
  final ProductCandidate buyOne;
  final List<ProductCandidate> products;
  final String disclaimer;

  factory Recommendations.fromJson(Map<String, dynamic> json) {
    return Recommendations(
      carePolicy: json['care_policy'] as String,
      morningCare: List<String>.from(json['morning_care'] as List<dynamic>),
      nightCare: List<String>.from(json['night_care'] as List<dynamic>),
      buyOne: ProductCandidate.fromJson(
        json['buy_one'] as Map<String, dynamic>,
      ),
      products: (json['products'] as List<dynamic>)
          .map(
            (item) => ProductCandidate.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      disclaimer: json['disclaimer'] as String,
    );
  }
}

class ProductCandidate {
  const ProductCandidate({
    required this.name,
    required this.brand,
    required this.category,
    required this.priceYen,
    required this.reasons,
  });

  final String name;
  final String brand;
  final String category;
  final int priceYen;
  final List<String> reasons;

  factory ProductCandidate.fromJson(Map<String, dynamic> json) {
    return ProductCandidate(
      name: json['name'] as String,
      brand: json['brand'] as String,
      category: json['category'] as String,
      priceYen: json['price_yen'] as int,
      reasons: List<String>.from(json['reasons'] as List<dynamic>),
    );
  }
}

class SkinLogItem {
  const SkinLogItem({
    required this.createdAt,
    required this.summary,
    required this.concerns,
  });

  final String createdAt;
  final String summary;
  final List<String> concerns;

  factory SkinLogItem.fromJson(Map<String, dynamic> json) {
    final analysis = json['analysis'] as Map<String, dynamic>;
    return SkinLogItem(
      createdAt: json['created_at'] as String,
      summary: analysis['summary'] as String,
      concerns: List<String>.from(
        analysis['detected_concerns'] as List<dynamic>,
      ),
    );
  }
}
