/**
 * Convert Google Credentials JSON for Vercel Environment Variable
 * This script properly escapes the JSON for use as an environment variable
 */

const fs = require('fs');
const path = require('path');

// Read the credentials file
const credentialsPath = path.join(__dirname, 'backend', 'google_credentials.json');
const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

// Convert to single-line JSON string
const singleLineJson = JSON.stringify(credentials);

console.log('\n✅ COPY THIS VALUE FOR VERCEL ENVIRONMENT VARIABLE:\n');
console.log('Variable Name: GOOGLE_APPLICATION_CREDENTIALS_JSON');
console.log('\nVariable Value (copy everything below this line):');
console.log('─────────────────────────────────────────────────────');
console.log(singleLineJson);
console.log('─────────────────────────────────────────────────────');
console.log('\n📋 Instructions:');
console.log('1. Copy the entire JSON string above (between the lines)');
console.log('2. Go to Vercel Dashboard → Settings → Environment Variables');
console.log('3. Add variable: GOOGLE_APPLICATION_CREDENTIALS_JSON');
console.log('4. Paste the copied value');
console.log('5. Save and redeploy\n');

