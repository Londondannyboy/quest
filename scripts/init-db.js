// Run this locally to initialize the database
// node scripts/init-db.js

console.log('🚀 Initializing Quest Core V2 Database...\n')

console.log('To initialize your database, run these commands:\n')
console.log('1. First, generate the Prisma client:')
console.log('   npx prisma generate\n')
console.log('2. Then push the schema to your database:')
console.log('   npx prisma db push\n')
console.log('3. (Optional) To view your database:')
console.log('   npx prisma studio\n')
console.log('Make sure you have DATABASE_URL and DIRECT_URL in your .env.local file!')
console.log('\nAfter running these commands, your database will be ready for users! 🎉')