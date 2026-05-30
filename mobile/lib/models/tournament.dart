import 'user.dart';

class Tournament {
  final int id;
  final String name;
  final String format;
  final String status;
  final bool isPublic;
  final bool hasPassword;
  final int maxParticipants;
  final int participantCount;
  final List<TournamentParticipant>? participants;

  Tournament({
    required this.id,
    required this.name,
    required this.format,
    required this.status,
    required this.isPublic,
    required this.hasPassword,
    required this.maxParticipants,
    required this.participantCount,
    this.participants,
  });

  factory Tournament.fromJson(Map<String, dynamic> json) {
    var pList = json['participants'] as List?;
    List<TournamentParticipant>? parsedParticipants;
    if (pList != null) {
      parsedParticipants = pList.map((e) => TournamentParticipant.fromJson(e)).toList();
    }

    return Tournament(
      id: json['id'],
      name: json['name'],
      format: json['format'],
      status: json['status'],
      isPublic: json['is_public'],
      hasPassword: json['has_password'] ?? false,
      maxParticipants: json['max_participants'],
      participantCount: json['participant_count'] ?? 0,
      participants: parsedParticipants,
    );
  }
}

class TournamentParticipant {
  final int id;
  final int tournamentId;
  final int userId;
  final int? seed;
  final User? user;

  TournamentParticipant({
    required this.id,
    required this.tournamentId,
    required this.userId,
    this.seed,
    this.user,
  });

  factory TournamentParticipant.fromJson(Map<String, dynamic> json) {
    return TournamentParticipant(
      id: json['id'],
      tournamentId: json['tournament_id'],
      userId: json['user_id'],
      seed: json['seed'],
      user: json['user'] != null ? User.fromJson(json['user']) : null,
    );
  }
}
