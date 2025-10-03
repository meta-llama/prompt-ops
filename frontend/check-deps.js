#!/usr/bin/env node

/**
 * Dependencies checker for llama-prompt-ops frontend
 * Checks for required system dependencies and environment setup
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for output
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, message) {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkCommand(command, name) {
  try {
    execSync(`${command} --version`, { stdio: 'pipe' });
    log('green', `✓ ${name} is available`);
    return true;
  } catch (error) {
    log('red', `✗ ${name} is not available`);
    return false;
  }
}

function checkFile(filePath, name) {
  if (fs.existsSync(filePath)) {
    log('green', `✓ ${name} exists`);
    return true;
  } else {
    log('red', `✗ ${name} missing`);
    return false;
  }
}

function checkNodeVersion() {
  try {
    const version = execSync('node --version', { encoding: 'utf8' }).trim();
    const majorVersion = parseInt(version.slice(1).split('.')[0]);
    if (majorVersion >= 18) {
      log('green', `✓ Node.js ${version} (>= 18)`);
      return true;
    } else {
      log('red', `✗ Node.js ${version} (< 18)`);
      return false;
    }
  } catch (error) {
    log('red', '✗ Node.js not available');
    return false;
  }
}

function checkPythonVersion() {
  try {
    const version = execSync('python --version', { encoding: 'utf8' }).trim();
    const versionMatch = version.match(/Python (\d+)\.(\d+)/);
    if (versionMatch) {
      const major = parseInt(versionMatch[1]);
      const minor = parseInt(versionMatch[2]);
      if (major >= 3 && minor >= 8) {
        log('green', `✓ ${version} (>= 3.8)`);
        return true;
      } else {
        log('red', `✗ ${version} (< 3.8)`);
        return false;
      }
    } else {
      log('red', '✗ Could not determine Python version');
      return false;
    }
  } catch (error) {
    // Try python3
    try {
      const version = execSync('python3 --version', { encoding: 'utf8' }).trim();
      const versionMatch = version.match(/Python (\d+)\.(\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1]);
        const minor = parseInt(versionMatch[2]);
        if (major >= 3 && minor >= 8) {
          log('green', `✓ ${version} (>= 3.8)`);
          return true;
        } else {
          log('red', `✗ ${version} (< 3.8)`);
          return false;
        }
      } else {
        log('red', '✗ Could not determine Python version');
        return false;
      }
    } catch (error2) {
      log('red', '✗ Python not available');
      return false;
    }
  }
}

function main() {
  log('blue', '🔍 Checking llama-prompt-ops frontend dependencies...\n');

  let allChecksPass = true;

  // System dependencies
  log('blue', '📋 System Dependencies:');
  allChecksPass &= checkNodeVersion();
  allChecksPass &= checkPythonVersion();
  allChecksPass &= checkCommand('npm', 'npm');
  allChecksPass &= checkCommand('git', 'git');
  console.log();

  // Project files
  log('blue', '📁 Project Files:');
  allChecksPass &= checkFile('package.json', 'package.json');
  allChecksPass &= checkFile('backend/main.py', 'backend/main.py');
  allChecksPass &= checkFile('backend/requirements.txt', 'backend/requirements.txt');
  console.log();

  // Node modules
  log('blue', '📦 Frontend Dependencies:');
  const nodeModulesExists = checkFile('node_modules', 'node_modules');
  if (!nodeModulesExists) {
    log('yellow', '💡 Run: npm install');
    allChecksPass = false;
  }
  console.log();

  // Python virtual environment
  log('blue', '🐍 Backend Dependencies:');
  const venvExists = checkFile('backend/venv', 'Python virtual environment');
  if (!venvExists) {
    log('yellow', '💡 Run: cd backend && python -m venv venv');
    allChecksPass = false;
  }
  console.log();

  // Environment configuration
  log('blue', '⚙️  Environment Configuration:');
  const envExists = checkFile('backend/.env', 'Environment configuration');
  if (!envExists) {
    log('yellow', '💡 Create backend/.env with your API keys');
    allChecksPass = false;
  }
  console.log();

  // Final result
  if (allChecksPass) {
    log('green', '✅ All dependencies are ready!');
    log('green', '🚀 Run: ./start-dev.sh or npm run dev');
  } else {
    log('red', '❌ Some dependencies are missing.');
    log('yellow', '📖 Check the README.md for setup instructions.');
  }
}

main();
