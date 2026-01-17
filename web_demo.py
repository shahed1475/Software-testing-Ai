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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from simple_demo import SimpleDemoRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global demo instance
demo_instance = None
current_execution = None

class WebDemoManager:
    """Manages the web demo execution and real-time updates"""
    
    def __init__(self):
        self.demo = SimpleDemoRunner()
        self.execution_status = {
            'running': False,
            'current_scenario': None,
            'progress': 0,
            'results': [],
            'start_time': None,
            'logs': [],
            'config': {}
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
            
            self.add_log("Starting Test Runner Agent System Demo", "info")
            
            # Initialize agents
            self.add_log("Initializing agents...", "info")
            await self.demo.simulate_agent_initialization()
            self.add_log("All agents initialized successfully!", "success")
            
            # Filter scenarios if specified
            scenarios = self.demo.demo_data['test_scenarios']
            if selected_scenarios:
                scenarios = [s for s in scenarios if s['name'] in selected_scenarios]
            
            total_scenarios = len(scenarios)
            
            # Run scenarios
            for i, scenario in enumerate(scenarios, 1):
                self.execution_status['current_scenario'] = scenario['name']
                self.execution_status['progress'] = int((i - 1) / total_scenarios * 100)
                
                self.add_log(f"Running Scenario {i}/{total_scenarios}: {scenario['name']}", "info")
                
                # Emit progress update
                socketio.emit('progress_update', {
                    'current_scenario': scenario['name'],
                    'progress': self.execution_status['progress'],
                    'scenario_index': i,
                    'total_scenarios': total_scenarios
                })
                
                # Run the scenario
                result = await self.demo.run_test_scenario(scenario)
                self.execution_status['results'].append(result)
                
                # Emit result update
                socketio.emit('scenario_complete', {
                    'scenario': scenario['name'],
                    'result': result
                })
                
                self.add_log(f"Completed {scenario['name']}", "success")
                
                # Short pause between scenarios
                if i < total_scenarios:
                    await asyncio.sleep(1)
            
            # Generate final report
            self.add_log("Generating summary report...", "info")
            self.execution_status['progress'] = 100
            self.execution_status['current_scenario'] = None
            
            self.add_log("Demo completed successfully!", "success")
            
            # Emit completion
            socketio.emit('demo_complete', {
                'results': self.execution_status['results'],
                'summary': self._generate_summary()
            })
            
        except Exception as e:
            self.add_log(f"Demo failed: {str(e)}", "error")
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
        total_findings = sum(len(r['results'].get('vulnerabilities', [])) for r in results)
        
        return {
            'total_scenarios': len(results),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'total_findings': total_findings,
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
    config = data.get('config', {})
    demo_manager.execution_status['config'] = config
    if config:
        target = config.get('target_url') or 'Not specified'
        environment = config.get('environment') or 'local'
        toggles = ', '.join(config.get('scan_toggles', [])) or 'none'
        demo_manager.add_log(
            f"Config set | target={target} | env={environment} | toggles={toggles}",
            "info"
        )
    
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
    demo_manager.add_log("Demo stopped by user", "warning")
    return jsonify({'message': 'Demo stopped'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    demo_manager.clients_connected += 1
    demo_manager.add_log(f"Client connected (Total: {demo_manager.clients_connected})", "info")
    
    # Send current status to new client
    emit('status_update', demo_manager.execution_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    demo_manager.clients_connected -= 1
    demo_manager.add_log(f"Client disconnected (Total: {demo_manager.clients_connected})", "info")

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
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;600;700&family=Sora:wght@400;500;600&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-0: #0b0f1a;
            --bg-1: #0e1526;
            --glass: rgba(16, 20, 32, 0.7);
            --glass-soft: rgba(19, 26, 42, 0.55);
            --text: #e7ecff;
            --muted: #9aa6c7;
            --accent: #4dd0e1;
            --accent-2: #f4b183;
            --success: #63d99f;
            --warning: #f3c96b;
            --danger: #ff7d7d;
            --border: rgba(120, 150, 210, 0.25);
            --glow: 0 0 28px rgba(77, 208, 225, 0.25);
        }
        body {
            font-family: 'Sora', 'Space Grotesk', sans-serif;
            background:
                radial-gradient(1200px 520px at 12% 12%, rgba(77, 208, 225, 0.18), transparent 60%),
                radial-gradient(900px 420px at 88% 16%, rgba(244, 177, 131, 0.16), transparent 60%),
                radial-gradient(600px 320px at 50% 100%, rgba(120, 140, 255, 0.12), transparent 60%),
                linear-gradient(160deg, var(--bg-0), var(--bg-1) 55%, #091320);
            color: var(--text);
            min-height: 100vh;
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image: radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px);
            background-size: 22px 22px;
            pointer-events: none;
            opacity: 0.35;
        }
        body::after {
            content: "";
            position: fixed;
            inset: -20%;
            background: radial-gradient(circle at 20% 20%, rgba(77, 208, 225, 0.08), transparent 35%),
                radial-gradient(circle at 80% 30%, rgba(244, 177, 131, 0.08), transparent 40%),
                radial-gradient(circle at 50% 80%, rgba(120, 140, 255, 0.08), transparent 45%);
            filter: blur(30px);
            animation: drift 18s ease-in-out infinite;
            pointer-events: none;
            opacity: 0.7;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 28px; position: relative; }
        .hero {
            background: linear-gradient(135deg, rgba(77, 208, 225, 0.18), rgba(244, 177, 131, 0.12));
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px 32px;
            margin-bottom: 24px;
            backdrop-filter: blur(16px);
            box-shadow: 0 18px 40px rgba(7, 12, 24, 0.6);
            animation: heroPulse 6s ease-in-out infinite;
        }
        .hero h1 { font-size: 2.6rem; font-weight: 700; letter-spacing: 0.5px; }
        .hero p { color: var(--muted); margin-top: 8px; font-size: 1.05rem; }
        .hero-badges { margin-top: 16px; display: flex; gap: 10px; flex-wrap: wrap; }
        .badge {
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 0.85rem;
            border: 1px solid var(--border);
            color: var(--text);
            background: rgba(18, 24, 38, 0.5);
        }
        .layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 20px; }
        .panel {
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 20px 22px;
            box-shadow: 0 20px 40px rgba(9, 14, 26, 0.55);
            backdrop-filter: blur(18px);
            animation: rise 0.7s ease both;
        }
        .stagger-1 { animation-delay: 0.06s; }
        .stagger-2 { animation-delay: 0.12s; }
        .stagger-3 { animation-delay: 0.18s; }
        .stagger-4 { animation-delay: 0.24s; }
        .stagger-5 { animation-delay: 0.3s; }
        .panel h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 12px; letter-spacing: 0.4px; }
        .panel-subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 14px; }
        .scenario-selection { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
        .scenario-item {
            padding: 10px 16px;
            border-radius: 999px;
            border: 1px solid rgba(77, 208, 225, 0.4);
            background: rgba(16, 25, 40, 0.55);
            color: var(--text);
            cursor: pointer;
            transition: all 0.25s ease;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .scenario-item .chip {
            color: var(--accent);
            border-color: rgba(77, 208, 225, 0.4);
            background: rgba(77, 208, 225, 0.08);
        }
        .scenario-item:hover { transform: translateY(-2px); box-shadow: var(--glow); }
        .scenario-item.selected {
            background: linear-gradient(135deg, rgba(77, 208, 225, 0.35), rgba(77, 208, 225, 0.12));
            border-color: rgba(77, 208, 225, 0.75);
        }
        .buttons { display: flex; gap: 12px; flex-wrap: wrap; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
        .field label { display: block; font-size: 0.82rem; color: var(--muted); margin-bottom: 6px; }
        .field input,
        .field select,
        .field textarea {
            width: 100%;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid rgba(120, 150, 210, 0.3);
            background: rgba(10, 16, 28, 0.7);
            color: var(--text);
            font-size: 0.9rem;
            outline: none;
            transition: border 0.2s ease, box-shadow 0.2s ease;
        }
        .field input:focus,
        .field select:focus,
        .field textarea:focus {
            border-color: rgba(77, 208, 225, 0.7);
            box-shadow: 0 0 0 3px rgba(77, 208, 225, 0.15);
        }
        .toggle-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
        .toggle {
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid rgba(120, 150, 210, 0.3);
            background: rgba(12, 20, 34, 0.7);
            color: var(--text);
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .toggle.active { background: rgba(99, 217, 159, 0.2); border-color: rgba(99, 217, 159, 0.6); }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip {
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            border: 1px solid rgba(120, 150, 210, 0.25);
            color: var(--muted);
        }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all 0.2s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, rgba(77, 208, 225, 0.95), rgba(77, 208, 225, 0.6));
            color: #031018;
            box-shadow: 0 10px 24px rgba(77, 208, 225, 0.25);
        }
        .btn-danger {
            background: linear-gradient(135deg, rgba(255, 125, 125, 0.9), rgba(255, 125, 125, 0.6));
            color: #2b0a0a;
        }
        .btn:hover:not(:disabled) { transform: translateY(-1px); filter: brightness(1.05); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .status-row { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
        .status-pill {
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(77, 208, 225, 0.18);
            border: 1px solid rgba(77, 208, 225, 0.4);
            font-size: 0.8rem;
            color: var(--text);
        }
        .progress-bar {
            width: 100%;
            height: 12px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
            margin: 12px 0 8px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, rgba(77, 208, 225, 1), rgba(99, 217, 159, 1));
            box-shadow: 0 0 16px rgba(77, 208, 225, 0.6);
            transition: width 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .progress-fill::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg, transparent 0%, rgba(255, 255, 255, 0.35) 35%, transparent 70%);
            transform: translateX(-60%);
            animation: sweep 2.4s linear infinite;
        }
        .logs {
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid rgba(120, 150, 210, 0.2);
            border-radius: 14px;
            padding: 16px;
            height: 380px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: #d5f7f2;
        }
        .log-entry { margin-bottom: 8px; animation: fadeInUp 0.35s ease; }
        .log-timestamp { color: rgba(154, 166, 199, 0.7); }
        .log-info { color: #9fe8ff; }
        .log-success { color: var(--success); }
        .log-warning { color: var(--warning); }
        .log-error { color: var(--danger); }
        .results { margin-top: 20px; display: none; }
        .result-card {
            background: var(--glass-soft);
            padding: 14px 16px;
            margin-top: 12px;
            border-radius: 12px;
            border: 1px solid rgba(120, 150, 210, 0.2);
        }
        .result-success { border-left: 3px solid var(--success); }
        .result-warning { border-left: 3px solid var(--warning); }
        .result-error { border-left: 3px solid var(--danger); }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
        }
        .metric-card {
            background: var(--glass-soft);
            padding: 16px;
            border-radius: 14px;
            border: 1px solid rgba(120, 150, 210, 0.2);
            text-align: left;
        }
        .metric-value { font-size: 1.6rem; font-weight: 700; color: var(--accent); }
        .metric-label { color: var(--muted); margin-top: 6px; font-size: 0.85rem; }
        @keyframes rise {
            from { opacity: 0; transform: translateY(14px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes sweep {
            0% { transform: translateX(-60%); }
            60% { transform: translateX(60%); }
            100% { transform: translateX(60%); }
        }
        @keyframes drift {
            0% { transform: translate3d(0, 0, 0); }
            50% { transform: translate3d(-2%, 1.5%, 0); }
            100% { transform: translate3d(0, 0, 0); }
        }
        @keyframes heroPulse {
            0% { box-shadow: 0 18px 40px rgba(7, 12, 24, 0.6); }
            50% { box-shadow: 0 24px 48px rgba(7, 12, 24, 0.75); }
            100% { box-shadow: 0 18px 40px rgba(7, 12, 24, 0.6); }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { animation: none !important; transition: none !important; }
        }
        @media (max-width: 980px) {
            .layout { grid-template-columns: 1fr; }
            .hero h1 { font-size: 2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>Test Runner Agent System</h1>
            <p>Real-time test execution, orchestration, and monitoring</p>
            <div class="hero-badges">
                <div class="badge">Live demo</div>
                <div class="badge">Streaming logs</div>
                <div class="badge">Scenario orchestration</div>
            </div>
        </div>

        <div class="layout">
            <div class="column left">
                <div class="panel controls stagger-1">
                    <h3>Test Configuration</h3>
                    <div class="panel-subtitle">Point to your app or server, then choose the scenario suite.</div>
                    <div class="form-grid">
                        <div class="field">
                            <label for="targetUrl">Target URL</label>
                            <input id="targetUrl" type="url" placeholder="https://app.example.com" />
                        </div>
                        <div class="field">
                            <label for="environment">Environment</label>
                            <select id="environment">
                                <option value="local">Local</option>
                                <option value="staging">Staging</option>
                                <option value="production">Production</option>
                            </select>
                        </div>
                        <div class="field">
                            <label for="authType">Authentication</label>
                            <select id="authType">
                                <option value="none">None</option>
                                <option value="basic">Basic</option>
                                <option value="token">Bearer Token</option>
                            </select>
                        </div>
                        <div class="field">
                            <label for="authValue">Auth Value</label>
                            <input id="authValue" type="password" placeholder="username:password or token" />
                        </div>
                    </div>
                    <div class="toggle-grid" id="scanToggles">
                        <div class="toggle" data-toggle="crawl">Crawl</div>
                        <div class="toggle" data-toggle="auth">Auth Checks</div>
                        <div class="toggle" data-toggle="rate_limit">Rate Limit</div>
                        <div class="toggle" data-toggle="passive">Passive Scan</div>
                        <div class="toggle" data-toggle="aggressive">Aggressive Scan</div>
                    </div>
                    <div class="chips">
                        <div class="chip">Safe mode enabled</div>
                        <div class="chip">Scope validation active</div>
                        <div class="chip">Audit logging</div>
                    </div>
                    <div class="panel-subtitle" style="margin-top: 16px;">Scenario suite</div>
                    <div class="scenario-selection" id="scenarioSelection">
                        <!-- Scenarios will be loaded here -->
                    </div>
                    <div class="buttons">
                        <button class="btn btn-primary" id="startBtn" onclick="startDemo()">Start Demo</button>
                        <button class="btn btn-danger" id="stopBtn" onclick="stopDemo()" disabled>Stop Demo</button>
                    </div>
                </div>

                <div class="panel status-panel stagger-2">
                    <div class="status-row">
                        <h3>Execution Status</h3>
                        <div class="status-pill">Live</div>
                    </div>
                    <div id="currentScenario">Ready to start...</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                    </div>
                    <div id="progressText">0% Complete</div>
                </div>

                <div class="panel metrics stagger-3" id="metricsPanel" style="display: none;">
                    <h3>Run Metrics</h3>
                    <div class="metrics">
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
                        <div class="metric-card">
                            <div class="metric-value" id="findingsCount">0</div>
                            <div class="metric-label">Findings</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="column right">
                <div class="panel stagger-4">
                    <h3>Activity Stream</h3>
                    <div class="panel-subtitle">Real-time system logs and orchestration updates.</div>
                    <div class="logs">
                        <div id="logContainer">
                            <div class="log-entry log-info">
                                <span class="log-timestamp">[Ready]</span> System initialized. Select scenarios and start a run.
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel results stagger-5" id="resultsPanel">
                    <h3>Test Results</h3>
                    <div id="resultsContainer"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let selectedScenarios = [];
        let selectedToggles = new Set();
        let isRunning = false;

        // Load scenarios on page load
        window.addEventListener('load', () => {
            document.body.classList.add('is-ready');
        });
        fetch('/api/scenarios')
            .then(response => response.json())
            .then(scenarios => {
                const container = document.getElementById('scenarioSelection');
                scenarios.forEach(scenario => {
                    const div = document.createElement('div');
                    div.className = 'scenario-item';
                    const label = document.createElement('span');
                    label.textContent = scenario.name;
                    const tag = document.createElement('span');
                    tag.className = 'chip';
                    tag.textContent = scenario.type && scenario.type.startsWith('pentest') ? 'PenTest' : 'Functional';
                    div.appendChild(label);
                    div.appendChild(tag);
                    div.onclick = () => toggleScenario(scenario.name, div);
                    container.appendChild(div);
                });
            });

        document.querySelectorAll('#scanToggles .toggle').forEach(toggle => {
            toggle.addEventListener('click', () => {
                const key = toggle.dataset.toggle;
                if (selectedToggles.has(key)) {
                    selectedToggles.delete(key);
                    toggle.classList.remove('active');
                } else {
                    selectedToggles.add(key);
                    toggle.classList.add('active');
                }
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

        function getConfigPayload() {
            return {
                target_url: document.getElementById('targetUrl').value.trim(),
                environment: document.getElementById('environment').value,
                auth_type: document.getElementById('authType').value,
                auth_value: document.getElementById('authValue').value,
                scan_toggles: Array.from(selectedToggles)
            };
        }

        function startDemo() {
            if (isRunning) return;
            
            fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenarios: selectedScenarios, config: getConfigPayload() })
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
            let vulnerabilities = '';
            if (result.vulnerabilities && result.vulnerabilities.length) {
                const counts = result.vulnerabilities.reduce((acc, v) => {
                    const key = (v.severity || 'UNKNOWN').toUpperCase();
                    acc[key] = (acc[key] || 0) + 1;
                    return acc;
                }, {});
                vulnerabilities = `<p>Findings: ${Object.entries(counts).map(([k, v]) => `${k}:${v}`).join(' ')}</p>`;
            }
            card.innerHTML = `
                <h4>${data.scenario}</h4>
                <p>Tests: ${result.total_tests} | Passed: ${result.passed} | Failed: ${result.failed} | Duration: ${result.duration}s</p>
                <p>Coverage: ${result.coverage || 'N/A'}%</p>
                ${vulnerabilities}
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
            document.getElementById('findingsCount').textContent = summary.total_findings || 0;
            document.getElementById('metricsPanel').style.display = 'grid';
        });
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'demo.html', 'w', encoding='utf-8') as f:
        f.write(template_content)

def main():
    """Main function to run the web demo"""
    print("Starting Test Runner Agent System Web Demo...")
    
    # Create template
    create_demo_template()
    
    # Start the web server
    print("Web demo starting at http://localhost:5000")
    print("Open your browser and navigate to the URL above")
    print("Press Ctrl+C to stop the server")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nWeb demo stopped by user")

if __name__ == "__main__":
    main()

