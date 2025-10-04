#!/usr/bin/env python3
"""
Web Interface for Test Runner Agent System Demo
==============================================

A simple Flask web application that provides a live interface
to trigger and monitor test runs using the Test Runner Agent system.
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import eventlet

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from demo_test_runner import TestRunnerDemo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global demo instance
demo_instance = None
current_execution = None

class WebDemoManager:
    """Manages the web demo execution and real-time updates"""
    
    def __init__(self):
        self.demo = TestRunnerDemo()
        self.execution_status = {
            'running': False,
            'current_scenario': None,
            'progress': 0,
            'results': [],
            'start_time': None,
            'logs': []
        }
        self.clients_connected = 0
    
    def add_log(self, message: str, level: str = 'info'):
        """Add a log message and emit to connected clients"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.execution_status['logs'].append(log_entry)
        
        # Keep only last 100 logs
        if len(self.execution_status['logs']) > 100:
            self.execution_status['logs'] = self.execution_status['logs'][-100:]
        
        # Emit to all connected clients
        socketio.emit('log_update', log_entry)
    
    async def run_demo_with_updates(self, selected_scenarios: List[str] = None):
        """Run demo with real-time updates via WebSocket"""
        try:
            self.execution_status['running'] = True
            self.execution_status['start_time'] = datetime.now().isoformat()
            self.execution_status['results'] = []
            self.execution_status['logs'] = []
            
            self.add_log("🚀 Starting Test Runner Agent System Demo", "info")
            
            # Initialize agents
            self.add_log("📋 Initializing agents...", "info")
            await self.demo.initialize_agents()
            self.add_log("✅ All agents initialized successfully!", "success")
            
            # Filter scenarios if specified
            scenarios = self.demo.demo_data['test_scenarios']
            if selected_scenarios:
                scenarios = [s for s in scenarios if s['name'] in selected_scenarios]
            
            total_scenarios = len(scenarios)
            
            # Run scenarios
            for i, scenario in enumerate(scenarios, 1):
                self.execution_status['current_scenario'] = scenario['name']
                self.execution_status['progress'] = int((i - 1) / total_scenarios * 100)
                
                self.add_log(f"🎯 Running Scenario {i}/{total_scenarios}: {scenario['name']}", "info")
                
                # Emit progress update
                socketio.emit('progress_update', {
                    'current_scenario': scenario['name'],
                    'progress': self.execution_status['progress'],
                    'scenario_index': i,
                    'total_scenarios': total_scenarios
                })
                
                # Run the scenario
                result = await self.demo.run_demo_scenario(scenario)
                self.execution_status['results'].append(result)
                
                # Emit result update
                socketio.emit('scenario_complete', {
                    'scenario': scenario['name'],
                    'result': result
                })
                
                self.add_log(f"✅ Completed {scenario['name']}", "success")
                
                # Short pause between scenarios
                if i < total_scenarios:
                    await asyncio.sleep(1)
            
            # Generate final report
            self.add_log("📊 Generating summary report...", "info")
            await self.demo.generate_summary_report(self.execution_status['results'])
            
            self.execution_status['progress'] = 100
            self.execution_status['current_scenario'] = None
            
            self.add_log("🎉 Demo completed successfully!", "success")
            
            # Emit completion
            socketio.emit('demo_complete', {
                'results': self.execution_status['results'],
                'summary': self._generate_summary()
            })
            
        except Exception as e:
            self.add_log(f"❌ Demo failed: {str(e)}", "error")
            logger.exception("Demo execution failed")
        finally:
            self.execution_status['running'] = False
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate execution summary"""
        results = self.execution_status['results']
        if not results:
            return {}
        
        total_tests = sum(r['results']['total_tests'] for r in results)
        total_passed = sum(r['results']['passed'] for r in results)
        total_failed = sum(r['results']['failed'] for r in results)
        total_duration = sum(r['results']['duration'] for r in results)
        
        return {
            'total_scenarios': len(results),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'execution_time': time.time() - time.mktime(datetime.fromisoformat(self.execution_status['start_time']).timetuple()) if self.execution_status['start_time'] else 0
        }

# Initialize demo manager
demo_manager = WebDemoManager()

@app.route('/')
def index():
    """Main demo page"""
    return render_template('demo.html')

@app.route('/api/scenarios')
def get_scenarios():
    """Get available test scenarios"""
    return jsonify(demo_manager.demo.demo_data['test_scenarios'])

@app.route('/api/status')
def get_status():
    """Get current execution status"""
    return jsonify(demo_manager.execution_status)

@app.route('/api/start', methods=['POST'])
def start_demo():
    """Start the demo execution"""
    if demo_manager.execution_status['running']:
        return jsonify({'error': 'Demo is already running'}), 400
    
    data = request.get_json() or {}
    selected_scenarios = data.get('scenarios', [])
    
    # Start demo in background
    def run_demo():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(demo_manager.run_demo_with_updates(selected_scenarios))
        loop.close()
    
    thread = threading.Thread(target=run_demo)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Demo started successfully'})

@app.route('/api/stop', methods=['POST'])
def stop_demo():
    """Stop the demo execution"""
    demo_manager.execution_status['running'] = False
    demo_manager.add_log("⏹️ Demo stopped by user", "warning")
    return jsonify({'message': 'Demo stopped'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    demo_manager.clients_connected += 1
    demo_manager.add_log(f"👤 Client connected (Total: {demo_manager.clients_connected})", "info")
    
    # Send current status to new client
    emit('status_update', demo_manager.execution_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    demo_manager.clients_connected -= 1
    demo_manager.add_log(f"👤 Client disconnected (Total: {demo_manager.clients_connected})", "info")

# Create templates directory and HTML template
def create_demo_template():
    """Create the demo HTML template"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Runner Agent System - Live Demo</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .controls { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .scenario-selection { margin-bottom: 20px; }
        .scenario-item { display: inline-block; margin: 5px; padding: 10px 15px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 5px; cursor: pointer; transition: all 0.3s; }
        .scenario-item:hover { background: #2196f3; color: white; }
        .scenario-item.selected { background: #2196f3; color: white; }
        .buttons { text-align: center; }
        .btn { padding: 12px 24px; margin: 0 10px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; transition: all 0.3s; }
        .btn-primary { background: #4caf50; color: white; }
        .btn-primary:hover { background: #45a049; }
        .btn-danger { background: #f44336; color: white; }
        .btn-danger:hover { background: #da190b; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .status-panel { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .progress-bar { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #4caf50, #8bc34a); transition: width 0.3s; }
        .logs { background: #1e1e1e; color: #00ff00; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 14px; }
        .log-entry { margin-bottom: 5px; }
        .log-timestamp { color: #888; }
        .log-info { color: #00ff00; }
        .log-success { color: #00ff88; }
        .log-warning { color: #ffaa00; }
        .log-error { color: #ff4444; }
        .results { background: white; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .result-card { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2196f3; }
        .result-success { border-left-color: #4caf50; }
        .result-warning { border-left-color: #ff9800; }
        .result-error { border-left-color: #f44336; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #2196f3; }
        .metric-label { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Runner Agent System</h1>
            <p>Live Demo - Real-time Test Execution & Monitoring</p>
        </div>
        
        <div class="controls">
            <h3>Select Test Scenarios</h3>
            <div class="scenario-selection" id="scenarioSelection">
                <!-- Scenarios will be loaded here -->
            </div>
            <div class="buttons">
                <button class="btn btn-primary" id="startBtn" onclick="startDemo()">🚀 Start Demo</button>
                <button class="btn btn-danger" id="stopBtn" onclick="stopDemo()" disabled>⏹️ Stop Demo</button>
            </div>
        </div>
        
        <div class="status-panel">
            <h3>Execution Status</h3>
            <div id="currentScenario">Ready to start...</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%"></div>
            </div>
            <div id="progressText">0% Complete</div>
        </div>
        
        <div class="logs">
            <div id="logContainer">
                <div class="log-entry log-info">
                    <span class="log-timestamp">[Ready]</span> Test Runner Agent System initialized. Select scenarios and click Start Demo.
                </div>
            </div>
        </div>
        
        <div class="results" id="resultsPanel" style="display: none;">
            <h3>Test Results</h3>
            <div id="resultsContainer"></div>
        </div>
        
        <div class="metrics" id="metricsPanel" style="display: none;">
            <div class="metric-card">
                <div class="metric-value" id="totalTests">0</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="passRate">0%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="totalDuration">0s</div>
                <div class="metric-label">Duration</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="scenariosRun">0</div>
                <div class="metric-label">Scenarios</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let selectedScenarios = [];
        let isRunning = false;

        // Load scenarios on page load
        fetch('/api/scenarios')
            .then(response => response.json())
            .then(scenarios => {
                const container = document.getElementById('scenarioSelection');
                scenarios.forEach(scenario => {
                    const div = document.createElement('div');
                    div.className = 'scenario-item';
                    div.textContent = scenario.name;
                    div.onclick = () => toggleScenario(scenario.name, div);
                    container.appendChild(div);
                });
            });

        function toggleScenario(name, element) {
            if (selectedScenarios.includes(name)) {
                selectedScenarios = selectedScenarios.filter(s => s !== name);
                element.classList.remove('selected');
            } else {
                selectedScenarios.push(name);
                element.classList.add('selected');
            }
        }

        function startDemo() {
            if (isRunning) return;
            
            fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenarios: selectedScenarios })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    isRunning = true;
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                }
            });
        }

        function stopDemo() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    isRunning = false;
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                });
        }

        // Socket event handlers
        socket.on('log_update', function(log) {
            const container = document.getElementById('logContainer');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${log.level}`;
            entry.innerHTML = `<span class="log-timestamp">[${new Date(log.timestamp).toLocaleTimeString()}]</span> ${log.message}`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        });

        socket.on('progress_update', function(data) {
            document.getElementById('currentScenario').textContent = `Running: ${data.current_scenario}`;
            document.getElementById('progressFill').style.width = `${data.progress}%`;
            document.getElementById('progressText').textContent = `${data.progress}% Complete (${data.scenario_index}/${data.total_scenarios})`;
        });

        socket.on('scenario_complete', function(data) {
            const container = document.getElementById('resultsContainer');
            const card = document.createElement('div');
            const result = data.result.results;
            const status = result.failed > 0 ? 'warning' : 'success';
            
            card.className = `result-card result-${status}`;
            card.innerHTML = `
                <h4>${data.scenario}</h4>
                <p>Tests: ${result.total_tests} | Passed: ${result.passed} | Failed: ${result.failed} | Duration: ${result.duration}s</p>
                <p>Coverage: ${result.coverage || 'N/A'}%</p>
            `;
            container.appendChild(card);
            document.getElementById('resultsPanel').style.display = 'block';
        });

        socket.on('demo_complete', function(data) {
            isRunning = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('currentScenario').textContent = 'Demo completed!';
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('progressText').textContent = '100% Complete';
            
            // Update metrics
            const summary = data.summary;
            document.getElementById('totalTests').textContent = summary.total_tests || 0;
            document.getElementById('passRate').textContent = `${(summary.pass_rate || 0).toFixed(1)}%`;
            document.getElementById('totalDuration').textContent = `${summary.total_duration || 0}s`;
            document.getElementById('scenariosRun').textContent = summary.total_scenarios || 0;
            document.getElementById('metricsPanel').style.display = 'grid';
        });
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'demo.html', 'w') as f:
        f.write(template_content)

def main():
    """Main function to run the web demo"""
    print("🌐 Starting Test Runner Agent System Web Demo...")
    
    # Create template
    create_demo_template()
    
    # Start the web server
    print("🚀 Web demo starting at http://localhost:5000")
    print("📱 Open your browser and navigate to the URL above")
    print("⏹️  Press Ctrl+C to stop the server")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n⏹️  Web demo stopped by user")

if __name__ == "__main__":
    main()