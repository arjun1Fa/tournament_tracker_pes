class User {
  final int id;
  final String username;
  final String? email; // Sometimes null if not requested by admin
  final String? profilePicture;
  final String? platform;
  final String? favouriteClub;
  final bool isAdmin;
  final bool isSuspended;

  User({
    required this.id,
    required this.username,
    this.email,
    this.profilePicture,
    this.platform,
    this.favouriteClub,
    this.isAdmin = false,
    this.isSuspended = false,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      profilePicture: json['profile_picture'],
      platform: json['platform'],
      favouriteClub: json['favourite_club'],
      isAdmin: json['is_admin'] ?? false,
      isSuspended: json['is_suspended'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'profile_picture': profilePicture,
      'platform': platform,
      'favourite_club': favouriteClub,
      'is_admin': isAdmin,
      'is_suspended': isSuspended,
    };
  }
}
