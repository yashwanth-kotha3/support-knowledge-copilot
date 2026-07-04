# Evaluation Report — strategy: hybrid
Generated: 2026-07-04T05:24:26.404331

## Summary Metrics
- Correct retrieval rate: 100.0%
- Avg citation support rate: 20.0%
- Avg confidence score: 0.414
- No-answer refusal accuracy: 100.0%

## Per-Question Results

### Q: How do I reset my password?
**Answer:** To reset your password, go to Settings > Security and click "Reset Password". 

[fixed_window_0] [How to reset your password] [password_reset.md]
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['password_reset.md']
- Correct retrieval: True
- Citation support rate: 0.0%
- Confidence: 0.248 ({'retrieval_score': 0.62, 'citation_support_rate': 0.0, 'completeness_score': 0.0, 'declared_no_answer': False})

### Q: What does error code AUTH_401 mean?
**Answer:** Error code AUTH_401 means your API key is missing or invalid [715b330feb873faf].
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['api_auth.md']
- Correct retrieval: True
- Citation support rate: 100.0%
- Confidence: 0.928 ({'retrieval_score': 0.82, 'citation_support_rate': 1.0, 'completeness_score': 1.0, 'declared_no_answer': False})

### Q: How long is a password reset link valid for?
**Answer:** A password reset link is valid for 30 minutes. [fixed_window_0]
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['password_reset.md']
- Correct retrieval: True
- Citation support rate: 0.0%
- Confidence: 0.256 ({'retrieval_score': 0.64, 'citation_support_rate': 0.0, 'completeness_score': 0.0, 'declared_no_answer': False})

### Q: What is the refund policy for annual subscriptions?
**Answer:** I could not find this in the docs.
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: []
- Correct retrieval: None
- Citation support rate: 0.0%
- Confidence: 0.4 ({'retrieval_score': 0.3, 'citation_support_rate': 0.0, 'completeness_score': 0.5, 'declared_no_answer': True})

### Q: What prefix do live API keys start with?
**Answer:** Live API keys start with the prefix "sk*live*" [chunk_id b6222872f5b70079].
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['api_auth.md']
- Correct retrieval: True
- Citation support rate: 0.0%
- Confidence: 0.24 ({'retrieval_score': 0.6, 'citation_support_rate': 0.0, 'completeness_score': 0.0, 'declared_no_answer': False})