import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/tournament_provider.dart';

class CreateTournamentScreen extends ConsumerStatefulWidget {
  const CreateTournamentScreen({super.key});

  @override
  ConsumerState<CreateTournamentScreen> createState() => _CreateTournamentScreenState();
}

class _CreateTournamentScreenState extends ConsumerState<CreateTournamentScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _passwordController = TextEditingController();
  
  String _selectedFormat = 'league';
  bool _isPublic = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      final createTourney = ref.read(createTournamentProvider);
      final tournament = await createTourney({
        'name': _nameController.text.trim(),
        'format': _selectedFormat,
        'is_public': _isPublic,
        if (_passwordController.text.isNotEmpty) 'password': _passwordController.text,
      });

      if (mounted) {
        context.pop(); // Go back
        context.push('/tournaments/${tournament.id}');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error creating tournament: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Tournament'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Tournament Name',
                  hintText: 'e.g. Summer Cup 2026',
                  prefixIcon: Icon(Icons.emoji_events_outlined),
                ),
                validator: (v) => v!.isEmpty ? 'Name is required' : null,
              ),
              const SizedBox(height: 24),
              
              DropdownButtonFormField<String>(
                value: _selectedFormat,
                decoration: const InputDecoration(
                  labelText: 'Format',
                  prefixIcon: Icon(Icons.list_alt),
                ),
                items: const [
                  DropdownMenuItem(value: 'league', child: Text('EFL League (Round-Robin + Knockout)')),
                  DropdownMenuItem(value: 'knockout', child: Text('Single Elimination Knockout')),
                ],
                onChanged: (val) {
                  if (val != null) setState(() => _selectedFormat = val);
                },
              ),
              const SizedBox(height: 24),

              SwitchListTile(
                title: const Text('Public Tournament'),
                subtitle: const Text('Anyone can see and join'),
                value: _isPublic,
                onChanged: (val) => setState(() => _isPublic = val),
                contentPadding: EdgeInsets.zero,
              ),
              
              if (!_isPublic) ...[
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  decoration: const InputDecoration(
                    labelText: 'Join Password',
                    hintText: 'Required to join',
                    prefixIcon: Icon(Icons.lock_outline),
                  ),
                  validator: (v) => v!.isEmpty ? 'Password is required for private tournaments' : null,
                ),
              ],
              
              const SizedBox(height: 48),
              
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Create Tournament'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
