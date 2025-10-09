/**
 * Convert Google Credentials JSON for Vercel Environment Variable
 * This script base64 encodes the JSON for use as an environment variable
 */

const fs = require('fs');
const path = require('path');

// Read the credentials file
const credentialsPath = path.join(__dirname, 'backend', 'google_credentials.json');
const credentialsJson = fs.readFileSync(credentialsPath, 'utf8');

// Base64 encode the JSON
const base64Encoded = Buffer.from(credentialsJson).toString('base64');

console.log('\n✅ COPY THIS VALUE FOR VERCEL ENVIRONMENT VARIABLE:\n');
console.log('Variable Name: GOOGLE_APPLICATION_CREDENTIALS_JSON');
console.log('\nVariable Value (BASE64 ENCODED - copy everything below):');
console.log('─────────────────────────────────────────────────────');
console.log(base64Encoded);
console.log('─────────────────────────────────────────────────────');
console.log('\n📋 Instructions:');
console.log('1. Copy the entire base64 string above (between the lines)');
console.log('2. Go to Vercel Dashboard → Settings → Environment Variables');
console.log('3. Find GOOGLE_APPLICATION_CREDENTIALS_JSON and EDIT it');
console.log('4. Paste the new base64 value');
console.log('5. Save and redeploy\n');

