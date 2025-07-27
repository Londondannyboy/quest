// Debug script to check environment variables
console.log('=== Environment Variables Debug ===\n');

// Check for any database-related variables
const envVars = Object.keys(process.env);
const dbRelated = envVars.filter(key => 
  key.includes('DATABASE') || 
  key.includes('POSTGRES') || 
  key.includes('NEON') ||
  key.includes('DB') ||
  key.includes('URL')
);

console.log('Database-related environment variables:');
dbRelated.forEach(key => {
  const value = process.env[key];
  if (value && value.includes('postgresql://')) {
    console.log(`${key}: [PostgreSQL URL found]`);
  } else {
    console.log(`${key}: ${value?.substring(0, 20)}...`);
  }
});

console.log('\nAll environment variables:');
envVars.sort().forEach(key => {
  if (!key.includes('PATH') && !key.includes('npm_')) {
    console.log(`- ${key}`);
  }
});