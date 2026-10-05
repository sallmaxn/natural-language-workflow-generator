import json
import logging
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .executor import execute_workflow
from .llm import generate_workflow
from .models import Workflow
from .validator import validate_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Natural Language Workflow Generator", description="Generate, validate, and execute safe business workflows")


class WorkflowRequest(BaseModel):
    requirement: str = Field(min_length=3, max_length=5000)


class ExecuteRequest(BaseModel):
    workflow: Workflow
    approvals: Dict[str, bool] = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(request: WorkflowRequest):
    try:
        workflow = generate_workflow(request.requirement.strip())
    except Exception as exc:
        logger.exception("Workflow generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    validation = validate_workflow(workflow)
    results = execute_workflow(workflow) if validation["valid"] else []
    return {"workflow": workflow.model_dump(), "validation": validation, "results": results}


@app.post("/execute")
def execute(request: ExecuteRequest):
    validation = validate_workflow(request.workflow)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail={"message": "Workflow validation failed", "errors": validation["errors"]})
    return {"validation": validation, "results": execute_workflow(request.workflow, request.approvals)}


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(PAGE)


PAGE = r'''<!DOCTYPE html>
<html>
<head>
<title>AI Workflow Generator</title>
<style>
body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 40px; }
.container { max-width: 1000px; margin: auto; }
h1 { color: #222; }
.subtitle { color: #666; }
textarea { width: 100%; height: 150px; padding: 15px; font-size: 16px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; }
button { margin-top: 15px; padding: 12px 25px; border: none; border-radius: 7px; background: #2563eb; color: white; font-size: 16px; cursor: pointer; }
button:hover { background: #1d4ed8; }
.card { background: white; padding: 25px; margin-top: 25px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.step { border-left: 4px solid #2563eb; padding: 12px 18px; margin: 12px 0; background: #f8fafc; }
.step-type { font-size: 13px; color: #2563eb; font-weight: bold; }
pre { background: #111827; color: #e5e7eb; padding: 20px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; }
.success { color: green; font-weight: bold; }
.error { color: red; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
<h1>🤖 AI Workflow Generator</h1>
<p class="subtitle">Convert natural-language business requirements into executable workflows.</p>
<div class="card">
<h2>Business Requirement</h2>
<textarea id="requirement" placeholder="Example: Process a customer order. If the order amount is above 10000, ask the manager for approval. If approved, create the order. Otherwise cancel it."></textarea>
<br><button id="generate" onclick="generateWorkflow()">Generate Workflow</button>
</div>
<div id="result"></div>
</div>
<script>
let currentWorkflow = null;
function escapeHtml(value) { return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
async function generateWorkflow() {
    const requirement = document.getElementById('requirement').value.trim();
    if (!requirement) { alert('Please enter a requirement.'); return; }
    const button = document.getElementById('generate');
    button.disabled = true;
    button.textContent = 'Generating...';
    document.getElementById('result').innerHTML = '<div class="card"><h2>Processing...</h2><p>AI is generating your workflow...</p></div>';
    try {
        const response = await fetch('/generate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({requirement:requirement})});
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
        currentWorkflow = data.workflow;
        renderWorkflow(data);
    } catch (error) {
        document.getElementById('result').innerHTML = '<div class="card"><p class="error">' + escapeHtml(error.message) + '</p></div>';
    } finally { button.disabled = false; button.textContent = 'Generate Workflow'; }
}
function renderWorkflow(data) {
    const w = data.workflow;
    let html = '<div class="card"><h2>Generated Workflow</h2><h3>' + escapeHtml(w.name) + '</h3><p>' + escapeHtml(w.description || '') + '</p>';
    w.steps.forEach(function (step, index) {
        html += '<div class="step"><div class="step-type">' + escapeHtml(step.type.toUpperCase()) + '</div><strong>' + (index + 1) + '. ' + escapeHtml(step.action || step.condition || step.type) + '</strong>';
        if (step.condition) html += '<p>Condition: ' + escapeHtml(step.condition) + '</p>';
        if (step.approver) html += '<p>Approver: ' + escapeHtml(step.approver) + '</p>';
        if (step.on_success) html += '<p>On success: ' + escapeHtml(step.on_success) + '</p>';
        if (step.on_failure) html += '<p>On failure: ' + escapeHtml(step.on_failure) + '</p>';
        html += '</div>';
    });
    html += '</div><div class="card"><h2>Validation</h2>';
    html += data.validation.valid ? '<p class="success">✓ Workflow Valid</p>' : '<p class="error">✕ Workflow Invalid</p><ul>' + data.validation.errors.map(function (e) { return '<li>' + escapeHtml(e) + '</li>'; }).join('') + '</ul>';
    html += '</div><div class="card"><h2>Execution Results</h2><div id="execution">' + executionHtml(data.results) + '</div></div>';
    html += '<div class="card"><h2>Workflow JSON</h2><button onclick="copyJson()">Copy JSON</button><pre>' + escapeHtml(JSON.stringify(w, null, 2)) + '</pre></div>';
    document.getElementById('result').innerHTML = html;
}
function executionHtml(results) {
    if (!results || !results.length) return '<p>No steps executed.</p>';
    return results.map(function (result) {
        let html = '<div class="step"><strong>' + escapeHtml(result.step_id || 'Workflow') + ' - ' + escapeHtml(result.status) + '</strong>';
        if (result.error) html += '<p class="error">' + escapeHtml(result.error) + '</p>';
        if (result.result) html += '<pre>' + escapeHtml(JSON.stringify(result.result, null, 2)) + '</pre>';
        if (result.status === 'pending' && result.result && result.result.approval_required) html += '<p>Human approval required · Approver: ' + escapeHtml(result.result.approver) + '</p><button onclick="decide(\'' + escapeHtml(result.step_id) + '\', true)">Approve</button><button onclick="decide(\'' + escapeHtml(result.step_id) + '\', false)">Reject</button>';
        return html + '</div>';
    }).join('');
}
async function decide(id, approved) {
    const area = document.getElementById('execution');
    area.innerHTML = '<p>Applying approval decision...</p>';
    try {
        const response = await fetch('/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({workflow:currentWorkflow, approvals:{[id]:approved}})});
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
        area.innerHTML = executionHtml(data.results);
    } catch (error) { area.innerHTML = '<p class="error">' + escapeHtml(error.message) + '</p>'; }
}
async function copyJson() {
    try { await navigator.clipboard.writeText(JSON.stringify(currentWorkflow, null, 2)); }
    catch (error) { alert('Could not copy JSON in this browser.'); }
}
</script>
</body>
</html>'''
