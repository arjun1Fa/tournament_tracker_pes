import 'dart:math';
import 'dart:io';

class OcrService {
  /// Simulates scanning an eFootball post-match screenshot and extracting stats.
  /// In a real app, this would upload the image file to a Google Cloud Vision endpoint,
  /// or run an on-device ML model (like Google ML Kit) to extract text, and then parse
  /// the stats using regex.
  Future<Map<String, dynamic>> scanMatchScreenshot(File imageFile) async {
    // Simulate network/processing delay
    await Future.delayed(const Duration(seconds: 3));

    // For now, we mock the OCR extraction with realistic random stats.
    // This allows the front-end to be fully functional before the real OCR is hooked up.
    final rand = Random();
    final score1 = rand.nextInt(5);
    final score2 = rand.nextInt(5);
    final possession = 40.0 + rand.nextInt(21); // 40-60%

    return {
      'score1': score1,
      'score2': score2,
      'team1_stats': {
        'possession': possession,
        'shots': score1 + rand.nextInt(6),
        'shots_on_target': score1 + rand.nextInt(3),
        'passes': 100 + rand.nextInt(50),
        'successful_passes': 80 + rand.nextInt(40),
        'fouls': rand.nextInt(5),
        'yellow_cards': rand.nextInt(2),
        'red_cards': 0,
        'corner_kicks': rand.nextInt(6),
      },
      'team2_stats': {
        'possession': 100.0 - possession,
        'shots': score2 + rand.nextInt(6),
        'shots_on_target': score2 + rand.nextInt(3),
        'passes': 100 + rand.nextInt(50),
        'successful_passes': 80 + rand.nextInt(40),
        'fouls': rand.nextInt(5),
        'yellow_cards': rand.nextInt(2),
        'red_cards': 0,
        'corner_kicks': rand.nextInt(6),
      }
    };
  }
}

final ocrServiceProvider = OcrService();
