---
inclusion: always
---

# Security Checklist

This checklist is automatically included in all Kiro sessions to ensure security best practices.

## Before ANY Commit

Verify these security requirements:

### 1. Secrets Management
- [ ] No hardcoded API keys, passwords, or tokens
- [ ] All secrets use environment variables
- [ ] `.env` files are in `.gitignore`
- [ ] Required secrets validated at startup

### 2. Input Validation
- [ ] All user inputs validated at system boundaries
- [ ] Schema-based validation used (Zod, Joi, Pydantic, etc.)
- [ ] Fail fast with clear error messages
- [ ] Never trust external data

### 3. SQL Injection Prevention
- [ ] Parameterized queries used (no string concatenation)
- [ ] ORM/query builder used correctly
- [ ] User input never directly in SQL strings

### 4. XSS Prevention
- [ ] HTML output sanitized (DOMPurify, bleach, etc.)
- [ ] User content escaped before rendering
- [ ] Content-Security-Policy headers set

### 5. Authentication & Authorization
- [ ] Authentication required for protected routes
- [ ] Authorization checks on all sensitive operations
- [ ] Session management secure (httpOnly, secure, sameSite)
- [ ] Password hashing with bcrypt/argon2

### 6. API Security
- [ ] Rate limiting on all endpoints
- [ ] CORS configured correctly
- [ ] CSRF protection enabled
- [ ] API keys rotated regularly

### 7. Error Handling
- [ ] Error messages don't leak sensitive data
- [ ] Stack traces not exposed in production
- [ ] Errors logged server-side with context

### 8. Dependencies
- [ ] Dependencies regularly updated
- [ ] Known vulnerabilities checked (`npm audit`, `pip-audit`)
- [ ] Minimal dependencies used

## Common Vulnerabilities to Check

### SQL Injection
```typescript
// ❌ VULNERABLE
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ SAFE
const query = 'SELECT * FROM users WHERE id = $1';
const result = await db.query(query, [userId]);
```

### XSS (Cross-Site Scripting)
```typescript
// ❌ VULNERABLE
element.innerHTML = userInput;

// ✅ SAFE
element.textContent = userInput;
// or use DOMPurify
element.innerHTML = DOMPurify.sanitize(userInput);
```

### Hardcoded Secrets
```typescript
// ❌ VULNERABLE
const apiKey = 'sk-1234567890abcdef';

// ✅ SAFE
const apiKey = process.env.API_KEY;
if (!apiKey) throw new Error('API_KEY not configured');
```

### Path Traversal
```typescript
// ❌ VULNERABLE
const filePath = path.join(uploadDir, req.body.filename);

// ✅ SAFE
const filename = path.basename(req.body.filename); // Remove path components
const filePath = path.join(uploadDir, filename);
```

### Command Injection
```typescript
// ❌ VULNERABLE
exec(`git clone ${userRepo}`);

// ✅ SAFE
execFile('git', ['clone', userRepo]);
```

## Security Review Triggers

Run security review when:
- Handling user authentication/authorization
- Processing user-uploaded files
- Executing system commands
- Making database queries
- Rendering user-generated content
- Handling payment information
- Before any production deployment

## If Security Issue Found

1. **STOP** - Don't commit vulnerable code
2. **Fix** - Address CRITICAL and HIGH severity issues immediately
3. **Rotate** - If secrets were exposed, rotate them immediately
4. **Review** - Check codebase for similar issues
5. **Test** - Verify fix doesn't break functionality

## Security Tools

### JavaScript/TypeScript
```bash
npm audit                 # Check for known vulnerabilities
npm audit fix            # Auto-fix vulnerabilities
npx eslint-plugin-security  # Security linting
```

### Python
```bash
pip-audit                # Check dependencies
bandit -r .              # Security linting
safety check             # Known vulnerabilities
```

### Go
```bash
go list -json -m all | nancy sleuth  # Dependency check
gosec ./...              # Security linting
```

### Java
```bash
mvn dependency-check:check  # OWASP dependency check
./gradlew dependencyCheckAnalyze  # Gradle
```

## Resources

For detailed security patterns, see:
- `skills/security-review/` - Comprehensive security guidelines
- `AGENTS.md` - security-reviewer agent guidelines
- OWASP Top 10: https://owasp.org/www-project-top-ten/
