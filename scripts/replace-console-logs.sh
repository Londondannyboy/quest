#!/bin/bash

# Replace console.log with logger.info
find src -name "*.ts" -o -name "*.tsx" | grep -v logger.ts | while read file; do
  if grep -q "console\." "$file"; then
    # Add logger import if not present
    if ! grep -q "from '@/lib/logger'" "$file"; then
      # Find the last import line
      last_import=$(grep -n "^import" "$file" | tail -1 | cut -d: -f1)
      if [ -n "$last_import" ]; then
        sed -i "${last_import}a\\import { logger } from '@/lib/logger'" "$file"
      else
        sed -i "1i\\import { logger } from '@/lib/logger'\\n" "$file"
      fi
    fi
    
    # Replace console statements
    sed -i "s/console\.log(/logger.info(/g" "$file"
    sed -i "s/console\.error(/logger.error(/g" "$file"
    sed -i "s/console\.warn(/logger.warn(/g" "$file"
    
    # Special replacements for tagged logs
    sed -i "s/logger\.info('\[AUDIO\]/logger.audio('/g" "$file"
    sed -i "s/logger\.info(\"\[AUDIO\]/logger.audio(\"/g" "$file"
    sed -i "s/logger\.info('\[WS\]/logger.ws('/g" "$file"
    sed -i "s/logger\.info(\"\[WS\]/logger.ws(\"/g" "$file"
    sed -i "s/logger\.info('\[WSManager\]/logger.ws('[WSManager]/g" "$file"
    
    echo "Updated: $file"
  fi
done

echo "Console log replacement complete!"