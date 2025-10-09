import React, { useState } from 'react';
import './App.css';

// Use environment variable for API URL, fallback to localhost for development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

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
  const [clients, setClients] = useState([]);
  const [loadingClients, setLoadingClients] = useState(false);
  const [showAddClientModal, setShowAddClientModal] = useState(false);
  const [newClientName, setNewClientName] = useState('');
  const [newClientCriteria, setNewClientCriteria] = useState({
    'Question 1': '',
    'Question 2': '',
    'Question 3': '',
    'Question 4': '',
    'Question 5': '',
    'Question 6': '',
    'Question 7': ''
  });

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

  const extractGid = (url) => {
    const match = url.match(/[#&]gid=([0-9]+)/);
    return match ? match[1] : '0'; // Default to first sheet (gid=0)
  };

  const loadClients = async () => {
    const sheetId = extractSheetId(spreadsheetUrl);
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL for loading clients');
      return;
    }

    setLoadingClients(true);
    addTerminalLog('Loading clients from Google Sheets...');
    try {
      const response = await fetch(`${API_URL}/clients?sheetId=${sheetId}`);
      const result = await response.json();
      
      console.log('Clients response:', result); // Debug log
      
      if (result.success) {
        setClients(result.clients);
        addTerminalLog(`✅ Loaded ${result.clients.length} clients: ${result.clients.join(', ')}`);
        } else {
        addTerminalLog('Error loading clients: ' + result.error);
      }
    } catch (error) {
      addTerminalLog(`Error loading clients: ${error.message}`);
      console.error('Client loading error:', error);
    } finally {
      setLoadingClients(false);
    }
  };

  const loadFromGoogleSheets = async () => {
    const sheetId = extractSheetId(spreadsheetUrl);
    const gid = extractGid(spreadsheetUrl);
    
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL');
      return;
    }

    // Clear previous data first
    setSheetApplications([]);
    setSelectedSheetRows([]);
    setLoadingSheets(true);
    addTerminalLog(`Loading unanalyzed applications from Google Sheets (tab gid=${gid})...`);
    
    try {
      // Add cache busting timestamp and gid
      const timestamp = new Date().getTime();
      const response = await fetch(`${API_URL}/sheets/unanalyzed?sheetId=${sheetId}&gid=${gid}&_t=${timestamp}`, {
        cache: 'no-store'
      });
      const result = await response.json();
      
      console.log('Loaded applications:', result); // Debug log
      
      if (result.success) {
        setSheetApplications(result.applications);
        addTerminalLog(`✅ Loaded ${result.count} unanalyzed applications from Google Sheets`);
        // Also load clients when loading sheets
        await loadClients();
      } else {
        addTerminalLog('Error loading from Google Sheets: ' + result.error);
      }
    } catch (error) {
      addTerminalLog(`Error loading from Google Sheets: ${error.message}`);
      console.error('Loading error:', error);
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

  const addNewClient = async () => {
    if (!newClientName.trim()) {
      addTerminalLog('Error: Client name is required');
      return;
    }

    const sheetId = extractSheetId(spreadsheetUrl);
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL');
      return;
    }

    try {
      addTerminalLog(`Adding new client: ${newClientName}...`);
      const response = await fetch(`${API_URL}/clients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clientName: newClientName,
          criteria: newClientCriteria,
          sheetId: sheetId
        })
      });

      const result = await response.json();

      if (result.success) {
        addTerminalLog(`✅ Client "${newClientName}" added successfully`);
        setShowAddClientModal(false);
        setNewClientName('');
        setNewClientCriteria({
          'Question 1': '',
          'Question 2': '',
          'Question 3': '',
          'Question 4': '',
          'Question 5': '',
          'Question 6': '',
          'Question 7': ''
        });
        // Reload clients
        await loadClients();
      } else {
        addTerminalLog(`Error adding client: ${result.error}`);
      }
    } catch (error) {
      addTerminalLog(`Error adding client: ${error.message}`);
    }
  };

  const deleteClient = async () => {
    if (!selectedClient) {
      addTerminalLog('Error: Please select a client to delete');
      return;
    }

    const sheetId = extractSheetId(spreadsheetUrl);
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete client "${selectedClient}"?`)) {
      return;
    }

    try {
      addTerminalLog(`Deleting client: ${selectedClient}...`);
      const response = await fetch(`${API_URL}/clients`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clientName: selectedClient,
          sheetId: sheetId
        })
      });

      const result = await response.json();

      if (result.success) {
        addTerminalLog(`✅ Client "${selectedClient}" deleted successfully`);
        setSelectedClient('');
        // Reload clients
        await loadClients();
      } else {
        addTerminalLog(`Error deleting client: ${result.error}`);
      }
    } catch (error) {
      addTerminalLog(`Error deleting client: ${error.message}`);
    }
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
    const gid = extractGid(spreadsheetUrl);
    
    if (!sheetId) {
      addTerminalLog('Error: Invalid spreadsheet URL');
      return;
    }

    setIsProcessing(true);
    setProcessingProgress(0);

    const BATCH_SIZE = 10; // Batch size to avoid serverless timeout
    const totalApplications = selectedSheetRows.length;
    
    // Check if we need to batch (10+ applications)
    if (totalApplications >= BATCH_SIZE) {
      addTerminalLog(`📦 Batching ${totalApplications} applications into groups of ${BATCH_SIZE} to avoid timeout...`);
      
      // Split into batches
      const batches = [];
      for (let i = 0; i < selectedSheetRows.length; i += BATCH_SIZE) {
        batches.push(selectedSheetRows.slice(i, i + BATCH_SIZE));
      }
      
      addTerminalLog(`Created ${batches.length} batches`);
      
      let totalAnalyzed = 0;
      let allFailedApplications = [];
      
      try {
        for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
          const batch = batches[batchIndex];
          const batchNum = batchIndex + 1;
          
          addTerminalLog(`\n🔄 Processing batch ${batchNum}/${batches.length} (${batch.length} applications)...`);
          setProcessingProgress((batchNum / batches.length) * 90);
          
          try {
            const response = await fetch(`${API_URL}/sheets/analyze`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                selectedRows: batch,
                client: selectedClient,
                jobDescription: jobDescription,
                supportingReferences: supportingReferences,
                sheetId: sheetId,
                gid: gid
              })
            });

            if (!response.ok) {
              throw new Error(`Batch ${batchNum} failed: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
              totalAnalyzed += result.analyzed_count;
              addTerminalLog(`✅ Batch ${batchNum} complete: ${result.analyzed_count} analyzed, ${result.failed_count} failed`);
              
              // Collect failed applications
              if (result.failed && result.failed.length > 0) {
                allFailedApplications = [...allFailedApplications, ...result.failed];
              }
            } else {
              addTerminalLog(`❌ Batch ${batchNum} error: ${result.error}`);
              // Add all batch rows to failed
              batch.forEach(row => {
                const app = sheetApplications.find(a => a.row_number === row);
                if (app) {
                  allFailedApplications.push({
                    row: row,
                    name: `${app.first_name} ${app.surname}`,
                    error: result.error || 'Batch processing failed'
                  });
                }
              });
            }
          } catch (error) {
            addTerminalLog(`❌ Batch ${batchNum} error: ${error.message}`);
            // Add all batch rows to failed
            batch.forEach(row => {
              const app = sheetApplications.find(a => a.row_number === row);
              if (app) {
                allFailedApplications.push({
                  row: row,
                  name: `${app.first_name} ${app.surname}`,
                  error: error.message
                });
              }
            });
          }
        }
        
        setProcessingProgress(100);
        addTerminalLog(`\n🎉 All batches complete! ${totalAnalyzed} applications analyzed total`);
        
        // Show failed applications modal if any failed
        if (allFailedApplications.length > 0) {
          setFailedApplications(allFailedApplications);
          setShowFailedModal(true);
        }
        
        // Reload to show remaining unanalyzed
        await loadFromGoogleSheets();
        setSelectedSheetRows([]);
        
      } catch (error) {
        addTerminalLog(`Error during batch processing: ${error.message}`);
      }
      
    } else {
      // Single batch (less than 10 applications)
      addTerminalLog(`Analyzing ${totalApplications} selected applications...`);
      
      try {
        const progressInterval = setInterval(() => {
          setProcessingProgress(prev => {
            if (prev >= 90) return prev;
            return prev + Math.random() * 10;
          });
        }, 500);

        const response = await fetch(`${API_URL}/sheets/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            selectedRows: selectedSheetRows,
            client: selectedClient,
            jobDescription: jobDescription,
            supportingReferences: supportingReferences,
            sheetId: sheetId,
            gid: gid
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
          setSelectedSheetRows([]);
          
          // Show success summary
          const summary = result.results.map(r => `Row ${r.row}: ${r.name} - ${r.score}`).join('\n');
          addTerminalLog(`Results:\n${summary}`);
        } else {
          throw new Error(result.error || 'Analysis failed');
        }
      } catch (error) {
        addTerminalLog(`Error during analysis: ${error.message}`);
      }
    }
    
    setIsProcessing(false);
    setProcessingProgress(0);
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
              <div style={{display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px'}}>
                <select
                  id="client-select"
                  value={selectedClient}
                  onChange={handleClientChange}
                  className="client-dropdown"
                  style={{flex: 1}}
                >
                  <option value="">Choose a client...</option>
                  {clients.map(client => (
                    <option key={client} value={client}>{client}</option>
                  ))}
                </select>
                <button 
                  onClick={() => setShowAddClientModal(true)}
                  style={{padding: '8px 12px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', whiteSpace: 'nowrap'}}
                  title="Add new client"
                >
                  + Add
                </button>
                <button 
                  onClick={deleteClient}
                  disabled={!selectedClient}
                  style={{padding: '8px 12px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', opacity: selectedClient ? 1 : 0.5}}
                  title="Delete selected client"
                >
                  🗑️
                </button>
              </div>
              <button 
                onClick={loadClients}
                disabled={loadingClients}
                style={{width: '100%', padding: '8px', backgroundColor: '#4285F4', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px'}}
              >
                {loadingClients ? '⏳ Loading Clients...' : '🔄 Load Clients from Sheet'}
              </button>
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

      {/* Add Client Modal */}
      {showAddClientModal && (
        <div className="modal-overlay" onClick={() => setShowAddClientModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{maxWidth: '700px', maxHeight: '80vh', overflowY: 'auto'}}>
            <div className="modal-header">
              <h3>➕ Add New Client</h3>
              <button className="close-button" onClick={() => setShowAddClientModal(false)}>×</button>
            </div>
            
            <div className="modal-body">
              <div style={{marginBottom: '20px'}}>
                <label style={{display: 'block', fontWeight: 'bold', marginBottom: '8px'}}>Client Name:</label>
                <input
                  type="text"
                  value={newClientName}
                  onChange={(e) => setNewClientName(e.target.value)}
                  placeholder="e.g., EDF Trading - Graduate Scheme"
                  style={{width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px'}}
                />
                  </div>

              <div style={{marginBottom: '20px'}}>
                <h4 style={{marginBottom: '10px'}}>Scoring Criteria:</h4>
                {Object.keys(newClientCriteria).map((questionKey) => (
                  <div key={questionKey} style={{marginBottom: '15px'}}>
                    <label style={{display: 'block', fontWeight: 'bold', marginBottom: '5px', fontSize: '13px'}}>{questionKey}:</label>
                    <textarea
                      value={newClientCriteria[questionKey]}
                      onChange={(e) => setNewClientCriteria({...newClientCriteria, [questionKey]: e.target.value})}
                      placeholder={`Enter criteria for ${questionKey}...`}
                      rows="4"
                      style={{width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace'}}
                    />
                  </div>
                ))}
              </div>

              <div style={{display: 'flex', gap: '10px', justifyContent: 'flex-end'}}>
                <button 
                  onClick={() => setShowAddClientModal(false)}
                  style={{padding: '10px 20px', backgroundColor: '#ccc', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                >
                  Cancel
                </button>
                <button 
                  onClick={addNewClient}
                  disabled={!newClientName.trim()}
                  style={{padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', opacity: newClientName.trim() ? 1 : 0.5}}
                >
                  Add Client
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

