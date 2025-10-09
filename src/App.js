import React, { useState } from 'react';
import './App.css';

function App() {
  const [selectedClient, setSelectedClient] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [supportingReferences, setSupportingReferences] = useState('');
  const [terminalLogs, setTerminalLogs] = useState(['Welcome to Sifting Tool', 'Ready to analyze Google Sheets applications...']);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [sheetApplications, setSheetApplications] = useState([]);
  const [selectedSheetRows, setSelectedSheetRows] = useState([]);
  const [loadingSheets, setLoadingSheets] = useState(false);
  const [failedApplications, setFailedApplications] = useState([]);
  const [showFailedModal, setShowFailedModal] = useState(false);
  const [spreadsheetUrl, setSpreadsheetUrl] = useState('https://docs.google.com/spreadsheets/d/1jDJDQXPoZE6NTAqfTaCILv8ULXpM_vl5WeiEVSplChU/edit?gid=0#gid=0');

  const clients = [
    'EDF Trading - Internship',
    'EDF Trading - Graduate Scheme', 
    'Client C',
    'Client D',
    'Client E'
  ];

  const addTerminalLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalLogs(prev => [...prev, `[${timestamp}] ${message}`]);
  };

  const handleClientChange = (event) => {
    setSelectedClient(event.target.value);
    addTerminalLog(`Client selected: ${event.target.value}`);
  };

  const handleJobDescriptionChange = (event) => {
    setJobDescription(event.target.value);
  };

  const clearTerminal = () => {
    setTerminalLogs(['Terminal cleared', 'Ready for new logs...']);
    addTerminalLog('Terminal cleared by user');
  };

  const extractSheetId = (url) => {
    const match = url.match(/\/d\/([a-zA-Z0-9-_]+)/);
    return match ? match[1] : null;
  };

  const loadFromGoogleSheets = async () => {
    const sheetId = extractSheetId(spreadsheetUrl);
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL');
      return;
    }

    setLoadingSheets(true);
    addTerminalLog('Loading unanalyzed applications from Google Sheets...');
    
    try {
      const response = await fetch(`http://localhost:5000/sheets/unanalyzed?sheetId=${sheetId}`);
      const result = await response.json();
      
      if (result.success) {
        setSheetApplications(result.applications);
        setSelectedSheetRows([]);
        addTerminalLog(`Loaded ${result.count} unanalyzed applications from Google Sheets`);
      } else {
        addTerminalLog('Error loading from Google Sheets: ' + result.error);
      }
    } catch (error) {
      addTerminalLog(`Error loading from Google Sheets: ${error.message}`);
    } finally {
      setLoadingSheets(false);
    }
  };

  const toggleSheetRowSelection = (rowNumber) => {
    if (selectedSheetRows.includes(rowNumber)) {
      setSelectedSheetRows(selectedSheetRows.filter(r => r !== rowNumber));
    } else {
      setSelectedSheetRows([...selectedSheetRows, rowNumber]);
    }
  };

  const retryFailedApplications = () => {
    const failedRows = failedApplications.map(f => f.row);
    setSelectedSheetRows(failedRows);
    setShowFailedModal(false);
    addTerminalLog(`Retrying ${failedRows.length} failed applications...`);
  };

  const analyzeSelectedSheets = async () => {
    if (selectedSheetRows.length === 0) {
      addTerminalLog('Error: Please select at least one application');
      return;
    }
    
    if (!selectedClient || !jobDescription) {
      addTerminalLog('Error: Please select client and enter job description');
      return;
    }

    const sheetId = extractSheetId(spreadsheetUrl);
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL');
      return;
    }

    setIsProcessing(true);
    setProcessingProgress(0);
    addTerminalLog(`Analyzing ${selectedSheetRows.length} selected applications...`);
    
    try {
      const progressInterval = setInterval(() => {
        setProcessingProgress(prev => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 10;
        });
      }, 500);

      const response = await fetch('http://localhost:5000/sheets/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selectedRows: selectedSheetRows,
          client: selectedClient,
          jobDescription: jobDescription,
          supportingReferences: supportingReferences,
          sheetId: sheetId
        })
      });

      clearInterval(progressInterval);
      setProcessingProgress(100);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        addTerminalLog(`✅ Analysis complete! ${result.analyzed_count} applications analyzed and written to Google Sheets`);
        
        // Check for failed applications
        if (result.failed_count > 0) {
          setFailedApplications(result.failed);
          setShowFailedModal(true);
          addTerminalLog(`⚠️ Warning: ${result.failed_count} applications failed to analyze`);
        }
        
        // Refresh the list to remove analyzed applications
        await loadFromGoogleSheets();
        
        // Show success summary
        const summary = result.results.map(r => `Row ${r.row}: ${r.name} - ${r.score}`).join('\n');
        addTerminalLog(`Results:\n${summary}`);
      } else {
        throw new Error(result.error || 'Analysis failed');
      }
      
    } catch (error) {
      addTerminalLog(`Error during analysis: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setProcessingProgress(0);
    }
  };

  return (
    <div className="app">
      <div className="main-content">
        {/* First Column - Applications */}
        <div className="column">
          <div className="section-header">
            <h3>Applications</h3>
          </div>
          
          {/* Spreadsheet URL Input */}
          <div className="form-group" style={{marginBottom: '15px'}}>
            <label htmlFor="spreadsheet-url">Google Sheets URL:</label>
            <input
              type="text"
              id="spreadsheet-url"
              value={spreadsheetUrl}
              onChange={(e) => setSpreadsheetUrl(e.target.value)}
              placeholder="https://docs.google.com/spreadsheets/d/..."
              style={{width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd'}}
            />
          </div>

          {/* Google Sheets Button */}
          <button 
            onClick={loadFromGoogleSheets}
            className="sheets-button"
            disabled={loadingSheets}
            style={{marginBottom: '20px', width: '100%', padding: '12px', backgroundColor: '#34A853', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px'}}
          >
            {loadingSheets ? '⏳ Loading...' : '📊 Load from Google Sheets'}
          </button>

          {/* Show Google Sheets applications if loaded */}
          {sheetApplications.length > 0 && (
            <div className="sheets-applications" style={{marginBottom: '20px', maxHeight: '400px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px', padding: '10px'}}>
              <div style={{marginBottom: '10px', fontWeight: 'bold'}}>
                {sheetApplications.length} Unanalyzed Applications
                <button 
                  onClick={() => {
                    const allRows = sheetApplications.map(app => app.row_number);
                    setSelectedSheetRows(selectedSheetRows.length === allRows.length ? [] : allRows);
                  }}
                  style={{marginLeft: '10px', padding: '4px 8px', fontSize: '12px'}}
                >
                  {selectedSheetRows.length === sheetApplications.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              {sheetApplications.map(app => (
                <div key={app.row_number} style={{display: 'flex', alignItems: 'center', padding: '8px', borderBottom: '1px solid #eee', cursor: 'pointer'}} onClick={() => toggleSheetRowSelection(app.row_number)}>
                  <input 
                    type="checkbox" 
                    checked={selectedSheetRows.includes(app.row_number)}
                    onChange={() => toggleSheetRowSelection(app.row_number)}
                    style={{marginRight: '10px'}}
                  />
                  <div style={{flex: 1}}>
                    <div style={{fontWeight: 'bold'}}>{app.first_name} {app.surname}</div>
                    <div style={{fontSize: '12px', color: '#666'}}>{app.university} - {app.course}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Second Column - Client & Job Description */}
        <div className="column">
          <div className="section-header">
            <h3>Client & Job Details</h3>
          </div>
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="client-select">Select Client:</label>
              <select
                id="client-select"
                value={selectedClient}
                onChange={handleClientChange}
                className="client-dropdown"
              >
                <option value="">Choose a client...</option>
                {clients.map(client => (
                  <option key={client} value={client}>{client}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="job-description">Job Description:</label>
              <textarea
                id="job-description"
                value={jobDescription}
                onChange={handleJobDescriptionChange}
                placeholder="Enter job description here..."
                className="job-description"
                rows="8"
              />
            </div>

            <div className="form-group">
              <label htmlFor="supporting-references">Supporting References (Optional):</label>
              <textarea
                id="supporting-references"
                value={supportingReferences}
                onChange={(e) => setSupportingReferences(e.target.value)}
                placeholder="Add any additional context, references, or criteria for the AI analysis..."
                className="supporting-references"
                rows="4"
              />
            </div>

            <button 
              onClick={analyzeSelectedSheets}
              className="process-button"
              disabled={selectedSheetRows.length === 0 || !selectedClient || !jobDescription}
            >
              {`Analyze ${selectedSheetRows.length} Selected`}
            </button>
          </div>
        </div>
      </div>

      {/* Terminal Status Bar */}
      <div className="terminal-bar">
        <div className="terminal-header">
          <div className="terminal-title">Status Log</div>
          <div className="terminal-controls">
            <button className="terminal-btn" onClick={clearTerminal}>Clear</button>
          </div>
        </div>
        <div className="terminal-content">
          {terminalLogs.map((log, index) => (
            <div key={index} className="terminal-line">
              {log}
            </div>
          ))}
          {isProcessing && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${processingProgress}%` }}
                ></div>
              </div>
              <span className="progress-text">{Math.round(processingProgress)}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Failed Applications Modal */}
      {showFailedModal && (
        <div className="modal-overlay" onClick={() => setShowFailedModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{maxWidth: '600px'}}>
            <div className="modal-header">
              <h3>⚠️ Some Applications Failed</h3>
              <button className="close-button" onClick={() => setShowFailedModal(false)}>×</button>
            </div>
            
            <div className="modal-body">
              <p style={{marginBottom: '15px'}}>
                {failedApplications.length} application(s) could not be analyzed. This might happen if the AI response format was unexpected.
              </p>
              
              <div style={{maxHeight: '300px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px', padding: '10px', marginBottom: '20px'}}>
                {failedApplications.map((failed, idx) => (
                  <div key={idx} style={{padding: '8px', borderBottom: '1px solid #eee'}}>
                    <div style={{fontWeight: 'bold'}}>Row {failed.row}: {failed.name}</div>
                    <div style={{fontSize: '12px', color: '#666', marginTop: '4px'}}>Error: {failed.error}</div>
                  </div>
                ))}
              </div>

              <div style={{display: 'flex', gap: '10px', justifyContent: 'flex-end'}}>
                <button 
                  onClick={() => setShowFailedModal(false)}
                  style={{padding: '10px 20px', backgroundColor: '#ccc', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                >
                  Skip
                </button>
                <button 
                  onClick={retryFailedApplications}
                  style={{padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                >
                  Retry Failed ({failedApplications.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

