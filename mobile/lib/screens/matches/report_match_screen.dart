import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import '../../providers/match_provider.dart';
import '../../services/ocr_service.dart';

class ReportMatchScreen extends ConsumerStatefulWidget {
  final int matchId;

  const ReportMatchScreen({super.key, required this.matchId});

  @override
  ConsumerState<ReportMatchScreen> createState() => _ReportMatchScreenState();
}

class _ReportMatchScreenState extends ConsumerState<ReportMatchScreen> {
  final _picker = ImagePicker();
  final _teamNameController = TextEditingController();
  final _opponentNameController = TextEditingController();
  
  File? _screenshot;
  bool _isScanning = false;
  bool _isSubmitting = false;
  Map<String, dynamic>? _scannedData;
  String _myTeam = 'team1'; // 'team1' or 'team2'

  @override
  void dispose() {
    _teamNameController.dispose();
    _opponentNameController.dispose();
    super.dispose();
  }

  Future<void> _pickAndScanImage() async {
    final picked = await _picker.pickImage(source: ImageSource.gallery);
    if (picked == null) return;

    setState(() {
      _screenshot = File(picked.path);
      _isScanning = true;
      _scannedData = null;
    });

    try {
      final data = await ocrServiceProvider.scanMatchScreenshot(_screenshot!);
      if (mounted) {
        setState(() {
          _scannedData = data;
          _isScanning = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isScanning = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('OCR Failed: $e')));
      }
    }
  }

  Future<void> _submitReport() async {
    if (_scannedData == null) return;
    if (_teamNameController.text.trim().isEmpty || _opponentNameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter team names')));
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final reportFn = ref.read(reportMatchProvider);
      final payload = {
        'my_team': _myTeam,
        'team1_name': _myTeam == 'team1' ? _teamNameController.text.trim() : _opponentNameController.text.trim(),
        'team2_name': _myTeam == 'team2' ? _teamNameController.text.trim() : _opponentNameController.text.trim(),
        'score1': _scannedData!['score1'],
        'score2': _scannedData!['score2'],
        'team1_stats': _scannedData!['team1_stats'],
        'team2_stats': _scannedData!['team2_stats'],
      };

      await reportFn(widget.matchId, payload);
      
      if (mounted) {
        context.pop();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Match reported! Waiting for opponent.')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Report failed: $e')));
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Match')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Screenshot Picker
            GestureDetector(
              onTap: _isScanning || _isSubmitting ? null : _pickAndScanImage,
              child: Container(
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade300, width: 2),
                  image: _screenshot != null
                      ? DecorationImage(image: FileImage(_screenshot!), fit: BoxFit.cover)
                      : null,
                ),
                child: _screenshot == null
                    ? Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.add_photo_alternate, size: 48, color: Colors.grey.shade500),
                          const SizedBox(height: 8),
                          Text('Upload post-match screenshot', style: TextStyle(color: Colors.grey.shade600)),
                        ],
                      )
                    : null,
              ),
            ),

            if (_isScanning) ...[
              const SizedBox(height: 32),
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: 16),
              const Center(child: Text('Extracting stats using AI OCR...')),
            ],

            if (_scannedData != null && !_isScanning) ...[
              const SizedBox(height: 32),
              Card(
                color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.05),
                elevation: 0,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Text('Extracted Result', style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text(
                        '${_scannedData!['score1']} - ${_scannedData!['score2']}',
                        style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 48),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Possession: ${_scannedData!['team1_stats']['possession'].toStringAsFixed(1)}% vs ${_scannedData!['team2_stats']['possession'].toStringAsFixed(1)}%',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              
              TextFormField(
                controller: _teamNameController,
                decoration: const InputDecoration(labelText: 'My In-Game Team Name (e.g. Arsenal)'),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _opponentNameController,
                decoration: const InputDecoration(labelText: 'Opponent In-Game Team Name'),
              ),
              const SizedBox(height: 16),
              
              DropdownButtonFormField<String>(
                initialValue: _myTeam,
                decoration: const InputDecoration(labelText: 'Which score is yours?'),
                items: [
                  DropdownMenuItem(value: 'team1', child: Text('Team 1 (Left - ${_scannedData!['score1']})')),
                  DropdownMenuItem(value: 'team2', child: Text('Team 2 (Right - ${_scannedData!['score2']})')),
                ],
                onChanged: (v) => setState(() => _myTeam = v!),
              ),
              
              const SizedBox(height: 32),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _submitReport,
                  child: _isSubmitting
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Submit Report'),
                ),
              ),
            ]
          ],
        ),
      ),
    );
  }
}
