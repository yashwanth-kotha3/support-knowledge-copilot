# Evaluation Report — strategy: dense_only
Generated: 2026-07-04T05:26:43.049759

## Summary Metrics
- Correct retrieval rate: 100.0%
- Avg citation support rate: 40.0%
- Avg confidence score: 0.480
- No-answer refusal accuracy: 100.0%

## Per-Question Results

### Q: How do I reset my password?
**Answer:** Go to Settings > Security. Click "Reset Password". [fixed_window_0]
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['password_reset.md']
- Correct retrieval: True
- Citation support rate: 0.0%
- Confidence: 0.0 ({'retrieval_score': 0.0, 'citation_support_rate': 0.0, 'completeness_score': 0.0, 'declared_no_answer': False})

### Q: What does error code AUTH_401 mean?
**Answer:** Error code AUTH_401 means your API key is missing or invalid. [715b330feb873faf]
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['api_auth.md']
- Correct retrieval: True
- Citation support rate: 100.0%
- Confidence: 0.6 ({'retrieval_score': 0.0, 'citation_support_rate': 1.0, 'completeness_score': 1.0, 'declared_no_answer': False})

### Q: How long is a password reset link valid for?
**Answer:** A password reset link is valid for 30 minutes [5e3e7d07c62918bd].
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['password_reset.md']
- Correct retrieval: True
- Citation support rate: 0.0%
- Confidence: 0.2 ({'retrieval_score': 0.0, 'citation_support_rate': 0.0, 'completeness_score': 1.0, 'declared_no_answer': False})

### Q: What is the refund policy for annual subscriptions?
**Answer:** I could not find this in the docs.
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: []
- Correct retrieval: None
- Citation support rate: 0.0%
- Confidence: 1.0 ({'retrieval_score': 0.0, 'citation_support_rate': 0.0, 'completeness_score': 0.5, 'declared_no_answer': True})

### Q: What prefix do live API keys start with?
**Answer:** Keys are prefixed with sk*live*. [b6222872f5b70079]
- Retrieved sources: ['api_auth.md', 'password_reset.md']
- Expected sources: ['api_auth.md']
- Correct retrieval: True
- Citation support rate: 100.0%
- Confidence: 0.6 ({'retrieval_score': 0.0, 'citation_support_rate': 1.0, 'completeness_score': 1.0, 'declared_no_answer': False})