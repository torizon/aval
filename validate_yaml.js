const fs = require('fs');
const YAML = require('yaml');

function validateYAML(filePath) {
  try {
    const fileContents = fs.readFileSync(filePath, 'utf8');
    const parsed = YAML.parse(fileContents);
    console.log('YAML is valid:', parsed);
  } catch (error) {
    console.error('YAML validation error:', error.message);
  }
}

validateYAML('pid_map.yaml');
