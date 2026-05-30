import 'user.dart';
import 'tournament.dart';

class Match {
  final int id;
  final int tournamentId;
  final String round;
  final int matchOrder;
  final int? player1Id;
  final int? player2Id;
  final String? team1Name;
  final String? team2Name;
  final int? score1;
  final int? score2;
  final String status;
  final bool verifiedByPlayer1;
  final bool verifiedByPlayer2;
  
  final User? player1;
  final User? player2;
  final Tournament? tournament;
  final List<MatchStats>? stats;

  Match({
    required this.id,
    required this.tournamentId,
    required this.round,
    required this.matchOrder,
    this.player1Id,
    this.player2Id,
    this.team1Name,
    this.team2Name,
    this.score1,
    this.score2,
    required this.status,
    required this.verifiedByPlayer1,
    required this.verifiedByPlayer2,
    this.player1,
    this.player2,
    this.tournament,
    this.stats,
  });

  factory Match.fromJson(Map<String, dynamic> json) {
    var statsList = json['stats'] as List?;
    List<MatchStats>? parsedStats;
    if (statsList != null) {
      parsedStats = statsList.map((e) => MatchStats.fromJson(e)).toList();
    }

    return Match(
      id: json['id'],
      tournamentId: json['tournament_id'],
      round: json['round'],
      matchOrder: json['match_order'],
      player1Id: json['player1_id'],
      player2Id: json['player2_id'],
      team1Name: json['team1_name'],
      team2Name: json['team2_name'],
      score1: json['score1'],
      score2: json['score2'],
      status: json['status'],
      verifiedByPlayer1: json['verified_by_player1'] ?? false,
      verifiedByPlayer2: json['verified_by_player2'] ?? false,
      player1: json['player1'] != null ? User.fromJson(json['player1']) : null,
      player2: json['player2'] != null ? User.fromJson(json['player2']) : null,
      tournament: json['tournament'] != null ? Tournament.fromJson(json['tournament']) : null,
      stats: parsedStats,
    );
  }
}

class MatchStats {
  final int id;
  final int matchId;
  final int userId;
  final String teamName;
  
  final double? possession;
  final int? shots;
  final int? shotsOnTarget;
  final int? fouls;
  final int? offsides;
  final int? cornerKicks;
  final int? freeKicks;
  final int? passes;
  final int? successfulPasses;
  final int? crosses;
  final int? interceptions;
  final int? tackles;
  final int? saves;

  MatchStats({
    required this.id,
    required this.matchId,
    required this.userId,
    required this.teamName,
    this.possession,
    this.shots,
    this.shotsOnTarget,
    this.fouls,
    this.offsides,
    this.cornerKicks,
    this.freeKicks,
    this.passes,
    this.successfulPasses,
    this.crosses,
    this.interceptions,
    this.tackles,
    this.saves,
  });

  factory MatchStats.fromJson(Map<String, dynamic> json) {
    return MatchStats(
      id: json['id'],
      matchId: json['match_id'],
      userId: json['user_id'],
      teamName: json['team_name'],
      possession: json['possession'] != null ? (json['possession'] as num).toDouble() : null,
      shots: json['shots'],
      shotsOnTarget: json['shots_on_target'],
      fouls: json['fouls'],
      offsides: json['offsides'],
      cornerKicks: json['corner_kicks'],
      freeKicks: json['free_kicks'],
      passes: json['passes'],
      successfulPasses: json['successful_passes'],
      crosses: json['crosses'],
      interceptions: json['interceptions'],
      tackles: json['tackles'],
      saves: json['saves'],
    );
  }
}
