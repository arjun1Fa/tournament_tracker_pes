class Match {
  final int id;
  final int tournamentId;
  final String roundName;
  final String stage;
  final int matchOrder;
  final int? player1Id;
  final String player1Name;
  final String? player1Team;
  final String? player1Image;
  final int? player2Id;
  final String player2Name;
  final String? player2Team;
  final String? player2Image;
  
  final int? score1;
  final int? score2;
  final int? possession1;
  final int? possession2;
  final int? shots1;
  final int? shots2;
  final int? shotsOnTarget1;
  final int? shotsOnTarget2;
  
  final String status;
  final int? betterPerformerSlot;
  final DateTime? completedAt;

  Match({
    required this.id,
    required this.tournamentId,
    required this.roundName,
    required this.stage,
    required this.matchOrder,
    this.player1Id,
    required this.player1Name,
    this.player1Team,
    this.player1Image,
    this.player2Id,
    required this.player2Name,
    this.player2Team,
    this.player2Image,
    this.score1,
    this.score2,
    this.possession1,
    this.possession2,
    this.shots1,
    this.shots2,
    this.shotsOnTarget1,
    this.shotsOnTarget2,
    required this.status,
    this.betterPerformerSlot,
    this.completedAt,
  });

  factory Match.fromJson(Map<String, dynamic> json) {
    return Match(
      id: json['id'],
      tournamentId: json['tournament_id'],
      roundName: json['round_name'],
      stage: json['stage'],
      matchOrder: json['match_order'],
      player1Id: json['player1_id'],
      player1Name: json['player1_name'],
      player1Team: json['player1_team'],
      player1Image: json['player1_image'],
      player2Id: json['player2_id'],
      player2Name: json['player2_name'],
      player2Team: json['player2_team'],
      player2Image: json['player2_image'],
      score1: json['score1'],
      score2: json['score2'],
      possession1: json['possession1'],
      possession2: json['possession2'],
      shots1: json['shots1'],
      shots2: json['shots2'],
      shotsOnTarget1: json['shots_on_target1'],
      shotsOnTarget2: json['shots_on_target2'],
      status: json['status'],
      betterPerformerSlot: json['better_performer_slot'],
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at']) : null,
    );
  }
}
