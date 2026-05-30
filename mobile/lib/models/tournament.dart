import 'player.dart';

class Tournament {
  final int id;
  final String name;
  final String status;
  final int playerCount;
  final DateTime? createdAt;
  final List<Player>? players;

  Tournament({
    required this.id,
    required this.name,
    required this.status,
    required this.playerCount,
    this.createdAt,
    this.players,
  });

  factory Tournament.fromJson(Map<String, dynamic> json) {
    return Tournament(
      id: json['id'],
      name: json['name'],
      status: json['status'],
      playerCount: json['player_count'] ?? 0,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
      players: json['players'] != null 
          ? (json['players'] as List).map((e) => Player.fromJson(e)).toList() 
          : null,
    );
  }
}
