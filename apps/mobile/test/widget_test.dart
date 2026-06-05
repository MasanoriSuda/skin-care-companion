import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:skin_care_companion/main.dart';

void main() {
  testWidgets('shows Japanese MVP diagnosis form', (WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(420, 920));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      SkinCareApp(apiClient: ApiClient(baseUrl: 'http://example.test')),
    );

    expect(find.text('肌ケア伴走'), findsOneWidget);
    expect(find.text('肌写真'), findsOneWidget);
    expect(find.text('問診'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, -520));
    await tester.pumpAndSettle();

    expect(find.text('診断して提案を見る'), findsOneWidget);
  });
}
