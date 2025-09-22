import React, { useState } from 'react';
import './App.css';

function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [selectedClient, setSelectedClient] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [supportingReferences, setSupportingReferences] = useState('');
  const [outputs, setOutputs] = useState([]);
  const [terminalLogs, setTerminalLogs] = useState(['Welcome to Sifting Tool', 'Ready for file upload...']);
  const [csvData, setCsvData] = useState(null);
  const [userCount, setUserCount] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [currentOutput, setCurrentOutput] = useState(null);
  const [showUserSelection, setShowUserSelection] = useState(false);
  const [tempSelectedUsers, setTempSelectedUsers] = useState([]);
  const [comparingOutputId, setComparingOutputId] = useState(null);
  const [clickedUser, setClickedUser] = useState(null);
  const [clickPosition, setClickPosition] = useState({ x: 0, y: 0 });
  const [detailedReasoning, setDetailedReasoning] = useState({});

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

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      addTerminalLog('Uploading file...');
      
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const csvText = e.target.result;
          
          // Better line splitting that handles newlines within quoted fields
          const lines = [];
          let currentLine = '';
          let inQuotes = false;
          
          for (let i = 0; i < csvText.length; i++) {
            const char = csvText[i];
            
            if (char === '"') {
              inQuotes = !inQuotes;
            } else if (char === '\n' && !inQuotes) {
              if (currentLine.trim()) {
                lines.push(currentLine.trim());
              }
              currentLine = '';
              continue;
            }
            currentLine += char;
          }
          
          // Add the last line if it exists
          if (currentLine.trim()) {
            lines.push(currentLine.trim());
          }
          
          // Better CSV parsing function that handles quoted fields
          const parseCSVLine = (line) => {
            const result = [];
            let current = '';
            let inQuotes = false;
            
            for (let i = 0; i < line.length; i++) {
              const char = line[i];
              
              if (char === '"') {
                inQuotes = !inQuotes;
              } else if (char === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
              } else {
                current += char;
              }
            }
            result.push(current.trim());
            return result;
          };
          
          const headers = parseCSVLine(lines[0]);
          
          const allData = lines.slice(1).map(line => {
            const values = parseCSVLine(line);
            const row = {};
            headers.forEach((header, index) => {
              row[header] = values[index] || '';
            });
            return row;
          });
          
          const data = allData.filter((row, index) => {
            // Check for User column (case insensitive)
            const userValue = row['User'] || row['user'] || row['USER'];
            
            // Look for patterns that indicate a real user entry
            // User entries are likely to be short identifiers, numbers, or names
            // Not long text responses
            const isShortIdentifier = userValue && userValue.length < 50 && 
                                    userValue.trim() !== '' && 
                                    userValue.trim() !== 'undefined' && 
                                    userValue.trim() !== 'null' &&
                                    !userValue.includes('EDF Trading') &&
                                    !userValue.includes('intern') &&
                                    !userValue.includes('market') &&
                                    !userValue.includes('understanding') &&
                                    !userValue.includes('appeals to me');
            
            return isShortIdentifier;
          });
          
          setCsvData(data);
          setUserCount(data.length);
          setUploadedFile(file);
          addTerminalLog(`File uploaded: ${file.name}`);
          addTerminalLog(`${data.length} user applications uploaded`);
        };
        reader.readAsText(file);
      } else {
        setTimeout(() => {
          setUploadedFile(file);
          addTerminalLog(`File uploaded: ${file.name}`);
        }, 1000);
      }
    }
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

  const formatAnalysis = (analysis, outputId) => {
    if (!analysis) return '';
    
    // Split by lines and look for user score patterns
    const lines = analysis.split('\n');
    let formatted = '';
    let inUserList = false;
    let foundUserScores = false;
    const isComparing = comparingOutputId === outputId;
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      // Look for user score patterns like "User 1 - Overall Score 9/15 - Q1: 3* Q2: 3* Q3: 3* - reason"
      // Handle both numbered list format (1. **User...) and regular format
      // Note: Q3 and Q5 may have "Yes" instead of numbers with *
      const userScoreMatch = trimmedLine.match(/\d+\.\s*\*\*User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/15.*Q1:\s*(\d+)\*.*Q2:\s*(\d+)\*.*Q3:\s*(\d+)\*.*-\s*(.+?)(?:\*\*)?$/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Overall\s+Score\s+(\d+)\/15.*Q1:\s*(\d+)\*.*Q2:\s*(\d+)\*.*Q3:\s*(\d+)\*.*-\s*(.+)/i) ||
                            trimmedLine.match(/\d+\.\s*\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+\*\*(\d+)\/15\*\*.*Q1:\s*\[(\w+)\].*Q2:\s*\[(\w+)\].*Q3:\s*\[(\w+)\].*Q4:\s*\[(\d+)\]\*.*Q5:\s*\[(\w+)\].*Q6:\s*\[(\d+)\]\*.*Q7:\s*\[(\d+)\]\*.*-\s*(.+?)(?:\*\*)?$/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Overall\s+Score\s+(\d+)\/15.*Q1:\s*\[(\w+)\].*Q2:\s*\[(\w+)\].*Q3:\s*\[(\w+)\].*Q4:\s*\[(\d+)\]\*.*Q5:\s*\[(\w+)\].*Q6:\s*\[(\d+)\]\*.*Q7:\s*\[(\d+)\]\*.*-\s*(.+)/i) ||
                            trimmedLine.match(/\d+\.\s*\*\*User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/30.*Q1:\s*(\d+)\*.*Q2:\s*(\d+)\*.*Q3:\s*(\d+)\*.*Q4:\s*(\d+)\*.*Q5:\s*(\d+)\*.*Q6:\s*(\d+)\*.*-\s*(.+?)(?:\*\*)?$/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Overall\s+Score\s+(\d+)\/30.*Q1:\s*(\d+)\*.*Q2:\s*(\d+)\*.*Q3:\s*(\d+)\*.*Q4:\s*(\d+)\*.*Q5:\s*(\d+)\*.*Q6:\s*(\d+)\*.*-\s*(.+)/i) ||
                            trimmedLine.match(/\d+\.\s*\*\*User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/25.*Q1:\s*(\d+)\*.*Q2:\s*(\d+)\*.*Q3:\s*(\d+)\*.*Q4:\s*(\d+)\*.*Q5:\s*(\d+)\*.*-\s*(.+?)(?:\*\*)?$/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Overall\s+Score\s+(\d+)\/25.*Q1:\s*(\d+)\*.*Q2:\s*(\d+)\*.*Q3:\s*(\d+)\*.*Q4:\s*(\d+)\*.*Q5:\s*(\d+)\*.*-\s*(.+)/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Score\s+(\d+)\*.*:\s*(.+)/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Score\s+(\d+)\*.*-\s*(.+)/i);
      
      if (userScoreMatch) {
        foundUserScores = true;
        const [, userNum, overallScore, q1, q2, q3, q4, q5, q6, q7, reason] = userScoreMatch;
        // For 3-question format: reason is at index 6, for 5-question format: reason is at index 8, for 6-question format: reason is at index 9, for 7-question format: reason is at index 10
        const actualReason = q7 ? reason : (q6 ? reason : (q4 && q5 ? reason : (userScoreMatch[6] || reason)));
        const isSelected = tempSelectedUsers.includes(parseInt(userNum));
        const isDisabled = !isSelected && tempSelectedUsers.length >= 3;
        
        // Fix undefined reason issue - show reason if available
        const reasonText = actualReason ? actualReason.trim().replace(/\*\*$/, '') : '';
        
        // Handle new format with overall score and individual question scores
        if (q1 && q2 && q3) {
          const totalScore = parseInt(overallScore);
          const questionScores = [parseInt(q1), parseInt(q2), parseInt(q3)];
          const avgScore = Math.round(totalScore / 3);
          const stars = '★'.repeat(avgScore) + '☆'.repeat(5 - avgScore);
          const maxScore = totalScore > 30 ? 35 : (totalScore > 25 ? 30 : (totalScore > 15 ? 25 : 15)); // Handle 3, 5, 6, and 7 question formats
          
          formatted += `<div class="user-score-item ${isComparing ? 'comparing' : ''}" data-user="${userNum}" data-total-score="${totalScore}" data-q1="${q1}" data-q2="${q2}" data-q3="${q3}">
            ${isComparing ? `<input type="checkbox" class="user-checkbox-inline" data-user="${userNum}" ${isSelected ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} />` : ''}
            <span class="user-number">User ${userNum}</span>
            <span class="score score-${getScoreClass(avgScore)}">${stars} (${totalScore}/${maxScore})</span>
            ${isComparing ? `<div class="question-breakdown">
              <span class="q-scores">Q1: ${q1}* Q2: ${q2}* Q3: ${q3}*</span>
            </div>` : ''}
            <span class="reason">${reasonText || 'No reason provided'}</span>
          </div>`;
        } else if (q1 && q2 && q3 && q4 && q5 && q6 && q7) {
          // Handle 7-question format for Graduate client
          const totalScore = parseInt(overallScore);
          // Only Q4, Q6, and Q7 are scored (1-5*), others are Yes/No informational
          const scoredQuestions = [parseInt(q4), parseInt(q6), parseInt(q7)];
          const avgScore = Math.round(totalScore / 3); // Only 3 questions are scored
          const stars = '★'.repeat(avgScore) + '☆'.repeat(5 - avgScore);
          
          formatted += `<div class="user-score-item ${isComparing ? 'comparing' : ''}" data-user="${userNum}" data-total-score="${totalScore}" data-q1="${q1}" data-q2="${q2}" data-q3="${q3}" data-q4="${q4}" data-q5="${q5}" data-q6="${q6}" data-q7="${q7}">
            ${isComparing ? `<input type="checkbox" class="user-checkbox-inline" data-user="${userNum}" ${isSelected ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} />` : ''}
            <span class="user-number">User ${userNum}</span>
            <span class="score score-${getScoreClass(avgScore)}">${stars} (${totalScore}/15)</span>
            ${isComparing ? `<div class="question-breakdown">
              <span class="q-scores">Q1: ${q1} Q2: ${q2} Q3: ${q3} Q4: ${q4}* Q5: ${q5} Q6: ${q6}* Q7: ${q7}*</span>
            </div>` : ''}
            <span class="reason">${reasonText || 'No reason provided'}</span>
          </div>`;
        } else if (q1 && q2 && q3 && q4 && q5 && q6) {
          // Handle 6-question format for Graduate client
          const totalScore = parseInt(overallScore);
          const questionScores = [parseInt(q1), parseInt(q2), parseInt(q3), parseInt(q4), parseInt(q5), parseInt(q6)];
          const avgScore = Math.round(totalScore / 6);
          const stars = '★'.repeat(avgScore) + '☆'.repeat(5 - avgScore);
          
          formatted += `<div class="user-score-item ${isComparing ? 'comparing' : ''}" data-user="${userNum}" data-total-score="${totalScore}" data-q1="${q1}" data-q2="${q2}" data-q3="${q3}" data-q4="${q4}" data-q5="${q5}" data-q6="${q6}">
            ${isComparing ? `<input type="checkbox" class="user-checkbox-inline" data-user="${userNum}" ${isSelected ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} />` : ''}
            <span class="user-number">User ${userNum}</span>
            <span class="score score-${getScoreClass(avgScore)}">${stars} (${totalScore}/30)</span>
            ${isComparing ? `<div class="question-breakdown">
              <span class="q-scores">Q1: ${q1}* Q2: ${q2}* Q3: ${q3}* Q4: ${q4}* Q5: ${q5}* Q6: ${q6}*</span>
            </div>` : ''}
            <span class="reason">${reasonText || 'No reason provided'}</span>
          </div>`;
        } else if (q1 && q2 && q3 && q4 && q5) {
          // Handle old 5-question format for backward compatibility
          const totalScore = parseInt(overallScore);
          const questionScores = [parseInt(q1), parseInt(q2), parseInt(q3), parseInt(q4), parseInt(q5)];
          const avgScore = Math.round(totalScore / 5);
          const stars = '★'.repeat(avgScore) + '☆'.repeat(5 - avgScore);
          
          formatted += `<div class="user-score-item ${isComparing ? 'comparing' : ''}" data-user="${userNum}" data-total-score="${totalScore}" data-q1="${q1}" data-q2="${q2}" data-q3="${q3}" data-q4="${q4}" data-q5="${q5}">
            ${isComparing ? `<input type="checkbox" class="user-checkbox-inline" data-user="${userNum}" ${isSelected ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} />` : ''}
            <span class="user-number">User ${userNum}</span>
            <span class="score score-${getScoreClass(avgScore)}">${stars} (${totalScore}/25)</span>
            ${isComparing ? `<div class="question-breakdown">
              <span class="q-scores">Q1: ${q1}* Q2: ${q2}* Q3: ${q3}* Q4: ${q4}* Q5: ${q5}*</span>
            </div>` : ''}
            <span class="reason">${reasonText || 'No reason provided'}</span>
          </div>`;
        } else {
          // Handle old format with single score
          const [, , singleScore, , , , , , singleReason] = userScoreMatch;
          const starScore = parseInt(singleScore || overallScore);
          const stars = '★'.repeat(starScore) + '☆'.repeat(5 - starScore);
          
          formatted += `<div class="user-score-item ${isComparing ? 'comparing' : ''}">
            ${isComparing ? `<input type="checkbox" class="user-checkbox-inline" data-user="${userNum}" ${isSelected ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} />` : ''}
            <span class="user-number">User ${userNum}</span>
            <span class="score score-${getScoreClass(starScore)}">${stars} (${starScore}/5)</span>
            <span class="reason">${singleReason || reasonText || 'No reason provided'}</span>
          </div>`;
        }
        inUserList = true;
      } else if (inUserList && trimmedLine && !trimmedLine.match(/User\s+\d+/i) && !trimmedLine.startsWith('###') && !trimmedLine.startsWith('**')) {
        // This might be a continuation of the reason
        formatted += `<span class="reason-continuation"> ${trimmedLine}</span>`;
      } else if (trimmedLine && !inUserList && !trimmedLine.startsWith('###') && !trimmedLine.startsWith('**')) {
        // Regular analysis text (skip headers)
        formatted += `<p>${trimmedLine}</p>`;
      }
    });
    
    if (!foundUserScores) {
      console.log('❌ No user scores found in analysis. Raw analysis:', analysis);
      return `<div class="analysis-error">No individual user scores found in analysis. The AI may have returned a summary instead of individual scores.</div>`;
    }
    
    return formatted || analysis;
  };

  const getScoreClass = (score) => {
    if (score >= 5) return 'excellent';
    if (score >= 4) return 'good';
    if (score >= 3) return 'fair';
    if (score >= 2) return 'poor';
    return 'very-poor';
  };

  const openUserSelection = (output) => {
    setCurrentOutput(output);
    setTempSelectedUsers([]);
    setComparingOutputId(output.id);
  };

  const closeUserSelection = () => {
    setComparingOutputId(null);
    setTempSelectedUsers([]);
    setCurrentOutput(null);
  };

  const toggleTempUserSelection = (userNum) => {
    if (tempSelectedUsers.includes(userNum)) {
      setTempSelectedUsers(tempSelectedUsers.filter(u => u !== userNum));
    } else if (tempSelectedUsers.length < 3) {
      setTempSelectedUsers([...tempSelectedUsers, userNum]);
    }
  };

  const confirmUserSelection = () => {
    if (tempSelectedUsers.length > 0) {
      setSelectedUsers(tempSelectedUsers);
      setComparingOutputId(null);
      setShowCompareModal(true);
    }
  };

  const closeCompareModal = () => {
    setShowCompareModal(false);
    setSelectedUsers([]);
    setCurrentOutput(null);
  };

  const getSelectedUsersData = () => {
    if (!currentOutput || !csvData) return [];
    return selectedUsers.map(userNum => {
      const userData = csvData.find((row, index) => index + 1 === userNum);
      const score = getUserScore(userNum);
      const overallScore = getUserOverallScore(userNum);
      return {
        userNum,
        data: userData || {},
        score: score,
        overallScore: overallScore
      };
    });
  };

  const getUserScore = (userNum) => {
    if (!currentOutput?.analysis) return null;
    
    const lines = currentOutput.analysis.split('\n');
    for (const line of lines) {
      const trimmedLine = line.trim();
      const userScoreMatch = trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/15/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/15/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/25/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/25/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/35/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/35/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/30/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/30/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Score\s+(\d+)\*:/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Score\s+(\d+)\*:/i) ||
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Score\s+(\d+)\*\s*-\s*/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Score\s+(\d+)\*\s*-\s*/i);
      
      if (userScoreMatch && parseInt(userScoreMatch[1]) === userNum) {
        const score = parseInt(userScoreMatch[2]);
        // If it's an overall score out of 15, 25, 30, or 35, convert to 1-5 scale for display
        if (score > 5) {
          return Math.round(score / (score > 30 ? 7 : (score > 25 ? 6 : (score > 15 ? 5 : 3))));
        }
        return score;
      }
    }
    return null;
  };

  const getUserOverallScore = (userNum) => {
    if (!currentOutput?.analysis) return null;
    
    const lines = currentOutput.analysis.split('\n');
    for (const line of lines) {
      const trimmedLine = line.trim();
      const userScoreMatch = trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/15/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/15/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/25/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/25/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/35/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/35/i) ||
                            trimmedLine.match(/\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+(\d+)\/30/i) || 
                            trimmedLine.match(/User\s+(\d+)\s*-\s*Overall\s+Score\s+(\d+)\/30/i);
      
      if (userScoreMatch && parseInt(userScoreMatch[1]) === userNum) {
        return parseInt(userScoreMatch[2]);
      }
    }
    return null;
  };

  const getDetailedReasoning = (userNum) => {
    if (!currentOutput?.analysis) return null;
    
    const lines = currentOutput.analysis.split('\n');
    let inDetailedSection = false;
    let reasoning = '';
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      if (trimmedLine.includes('DETAILED REASONING:')) {
        inDetailedSection = true;
        continue;
      }
      
      if (inDetailedSection && trimmedLine.startsWith(`User ${userNum}:`)) {
        reasoning = trimmedLine.replace(`User ${userNum}:`, '').trim();
        break;
      }
    }
    
    return reasoning || null;
  };

  const getShortJustification = (userNum) => {
    if (!currentOutput?.analysis) return null;
    
    const lines = currentOutput.analysis.split('\n');
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Look for the user score line with the short justification
      const userScoreMatch = trimmedLine.match(/\d+\.\s*\*\*User\s+(\d+)\*\*\s*-\s*Overall\s+Score\s+\*\*(\d+)\/15\*\*.*Q1:\s*\[(\w+)\].*Q2:\s*\[(\w+)\].*Q3:\s*\[(\w+)\].*Q4:\s*\[(\d+)\]\*.*Q5:\s*\[(\w+)\].*Q6:\s*\[(\d+)\]\*.*Q7:\s*\[(\d+)\]\*.*-\s*(.+?)(?:\*\*)?$/i) ||
                            trimmedLine.match(/.*User\s+(\d+).*Overall\s+Score\s+(\d+)\/15.*Q1:\s*\[(\w+)\].*Q2:\s*\[(\w+)\].*Q3:\s*\[(\w+)\].*Q4:\s*\[(\d+)\]\*.*Q5:\s*\[(\w+)\].*Q6:\s*\[(\d+)\]\*.*Q7:\s*\[(\d+)\]\*.*-\s*(.+)/i);
      
      if (userScoreMatch && parseInt(userScoreMatch[1]) === userNum) {
        return userScoreMatch[userScoreMatch.length - 1]; // Last group is the reason
      }
    }
    
    return null;
  };

  const processFile = async () => {
    if (!uploadedFile || !selectedClient || !jobDescription) {
      addTerminalLog('Error: Please fill in all required fields');
      return;
    }

    if (!csvData) {
      addTerminalLog('Error: No CSV data to process');
      return;
    }

    setIsProcessing(true);
    setProcessingProgress(0);
    addTerminalLog('Processing file with AI analysis...');
    
    try {
      // Simulate progress for large files
      const progressInterval = setInterval(() => {
        setProcessingProgress(prev => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 10;
        });
      }, 500);

      // Call the backend API for AI analysis
      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client: selectedClient,
          jobDescription: jobDescription,
          supportingReferences: supportingReferences,
          csvData: csvData, // Send ALL candidates, not just samples
          userCount: userCount
        })
      });

      clearInterval(progressInterval);
      setProcessingProgress(100);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Analysis failed');
      }

      addTerminalLog('AI analysis completed');
      
      const newOutput = {
        id: Date.now(),
        client: selectedClient,
        fileName: uploadedFile.name,
        description: jobDescription,
        userCount: userCount,
        status: 'AI Analysis Completed',
        timestamp: new Date().toLocaleTimeString(),
        analysis: result.analysis
      };
      
      setOutputs(prev => [...prev, newOutput]);
      addTerminalLog(`File processed successfully for ${selectedClient} - ${userCount} applications analyzed`);
      
    } catch (error) {
      addTerminalLog(`Error during processing: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setProcessingProgress(0);
    }
  };

  return (
    <div className="app" onClick={() => setClickedUser(null)}>
      <div className="main-content">
        {/* First Column - File Upload */}
        <div className="column">
          <div className="section-header">
            <h3>File Upload</h3>
          </div>
          <div className="upload-section">
            <div className="upload-area">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileUpload}
                className="file-input"
                accept=".pdf,.doc,.docx,.txt,.csv"
              />
              <label htmlFor="file-upload" className="upload-label">
                <div className="upload-icon">📁</div>
                <div className="upload-text">
                  {uploadedFile ? uploadedFile.name : 'Click to upload file'}
                </div>
                <div className="upload-hint">Supports: PDF, DOC, DOCX, TXT, CSV</div>
              </label>
            </div>
            {uploadedFile && (
              <div className="file-info">
                <div className="file-name">{uploadedFile.name}</div>
                <div className="file-size">{(uploadedFile.size / 1024).toFixed(1)} KB</div>
                {csvData && (
                  <div className="csv-info">
                    <div className="user-count">{userCount} user applications uploaded</div>
                    <div className="csv-headers">
                      <strong>Headers:</strong> {Object.keys(csvData[0] || {}).join(', ')}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
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
              onClick={processFile}
              className="process-button"
              disabled={!uploadedFile || !selectedClient || !jobDescription}
            >
              Process File
            </button>
          </div>
        </div>

        {/* Third Column - Outputs */}
        <div className="column">
          <div className="section-header">
            <h3>Outputs</h3>
          </div>
          <div className="outputs-section">
            {outputs.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📋</div>
                <div className="empty-text">No outputs yet</div>
                <div className="empty-hint">Process a file to see results here</div>
              </div>
            ) : (
              <div className="outputs-list">
                {outputs.map(output => (
                  <div key={output.id} className="output-item">
                    <div className="output-header">
                      <div className="output-client">{output.client}</div>
                      <div className="output-actions">
                        <button 
                          className="compare-button"
                          onClick={() => openUserSelection(output)}
                        >
                          Compare
                        </button>
                        <div className="output-status completed">{output.status}</div>
                      </div>
                    </div>
                    <div className="output-file">{output.fileName}</div>
                    {output.userCount && (
                      <div className="output-count">{output.userCount} applications analyzed</div>
                    )}
                    {output.analysis && (
                      <div className="output-analysis">
                        <strong>Analysis:</strong> 
                        <div 
                          className="analysis-content" 
                          dangerouslySetInnerHTML={{__html: formatAnalysis(output.analysis, output.id)}}
                          onClick={(e) => {
                            if (e.target.classList.contains('user-checkbox-inline')) {
                              const userNum = parseInt(e.target.dataset.user);
                              toggleTempUserSelection(userNum);
                            } else {
                              const userScoreItem = e.target.closest('.user-score-item');
                              if (userScoreItem && !comparingOutputId && !e.target.classList.contains('user-checkbox-inline')) {
                                const userNum = parseInt(userScoreItem.dataset.user);
                                const totalScore = userScoreItem.dataset.totalScore;
                                const q1 = userScoreItem.dataset.q1;
                                const q2 = userScoreItem.dataset.q2;
                                const q3 = userScoreItem.dataset.q3;
                                const q4 = userScoreItem.dataset.q4;
                                const q5 = userScoreItem.dataset.q5;
                                const q6 = userScoreItem.dataset.q6;
                                const q7 = userScoreItem.dataset.q7;
                                
                                if (userNum && totalScore) {
                                  const reasoning = getDetailedReasoning(userNum);
                                  setClickedUser({
                                    userNum,
                                    totalScore: parseInt(totalScore),
                                    q1: q1 ? parseInt(q1) : null,
                                    q2: q2 ? parseInt(q2) : null,
                                    q3: q3 ? parseInt(q3) : null,
                                    q4: q4 ? parseInt(q4) : null,
                                    q5: q5 ? parseInt(q5) : null,
                                    q6: q6 ? parseInt(q6) : null,
                                    q7: q7 ? parseInt(q7) : null,
                                    reasoning: reasoning
                                  });
                                  setClickPosition({
                                    x: e.clientX,
                                    y: e.clientY
                                  });
                                }
                              }
                            }
                          }}
                        />
                        {comparingOutputId === output.id && (
                          <div className="comparison-controls">
                            <div className="selection-info">
                              {tempSelectedUsers.length}/3 selected
                            </div>
                            <div className="comparison-actions">
                              <button 
                                className="confirm-button"
                                onClick={confirmUserSelection}
                                disabled={tempSelectedUsers.length === 0}
                              >
                                Compare Selected Users
                              </button>
                              <button 
                                className="cancel-button"
                                onClick={closeUserSelection}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    <div className="output-timestamp">{output.timestamp}</div>
                  </div>
                ))}
              </div>
            )}
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


      {/* Compare Modal */}
      {showCompareModal && (
        <div className="modal-overlay" onClick={closeCompareModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Compare Users - {currentOutput?.client}</h3>
              <button className="close-button" onClick={closeCompareModal}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="comparison-grid">
                {getSelectedUsersData().map(({ userNum, data, score, overallScore }) => (
                  <div key={userNum} className="user-comparison-card">
                    <div className="user-card-header">
                      <h4>
                        User {userNum}
                        {overallScore !== null ? (
                          <span className={`user-score-inline score-${getScoreClass(Math.round(overallScore / (overallScore > 15 ? 5 : 3)))}`}>
                            {'★'.repeat(Math.round(overallScore / (overallScore > 15 ? 5 : 3))) + '☆'.repeat(5 - Math.round(overallScore / (overallScore > 15 ? 5 : 3)))} ({overallScore}/{overallScore > 15 ? 25 : 15})
                          </span>
                        ) : score !== null ? (
                          <span className={`user-score-inline score-${getScoreClass(score)}`}>
                            {'★'.repeat(score) + '☆'.repeat(5 - score)} ({score}/5)
                          </span>
                        ) : null}
                      </h4>
                    </div>
                    <div className="user-card-content">
                      {getShortJustification(userNum) && (
                        <div className="comparison-short-reason">
                          <h5>Short Justification:</h5>
                          <p>{getShortJustification(userNum)}</p>
                        </div>
                      )}
                      {getDetailedReasoning(userNum) && (
                        <div className="comparison-reasoning">
                          <h5>Detailed AI Analysis:</h5>
                          <p>{getDetailedReasoning(userNum)}</p>
                        </div>
                      )}
                      {Object.entries(data).map(([key, value]) => (
                        <div key={key} className="field-comparison">
                          <strong>{key}:</strong>
                          <div className="field-value">{value || 'N/A'}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Click Popup */}
      {clickedUser && (
        <>
          <div className="popup-backdrop" onClick={() => setClickedUser(null)}></div>
          <div 
            className="click-popup"
            style={{
              position: 'fixed',
              left: Math.min(clickPosition.x + 10, window.innerWidth - 520),
              top: Math.min(clickPosition.y - 10, window.innerHeight - 400),
              zIndex: 1001
            }}
            onClick={(e) => e.stopPropagation()}
          >
          <div className="click-popup-content">
            <div className="click-popup-header">
              <h4>User {clickedUser.userNum}</h4>
              <button className="close-popup" onClick={() => setClickedUser(null)}>×</button>
            </div>
            <div className="click-popup-score">
              {clickedUser.q1 && clickedUser.q2 && clickedUser.q3 ? (
                <>
                  <div className="click-overall-score">
                    {clickedUser.totalScore}/{clickedUser.totalScore > 30 ? 35 : (clickedUser.totalScore > 25 ? 30 : (clickedUser.totalScore > 15 ? 25 : 15))}
                  </div>
                  <div className="click-question-scores">
                    Q1: {clickedUser.q1}* Q2: {clickedUser.q2}* Q3: {clickedUser.q3}*
                    {clickedUser.q4 && clickedUser.q5 && ` Q4: ${clickedUser.q4}* Q5: ${clickedUser.q5}*`}
                    {clickedUser.q6 && ` Q6: ${clickedUser.q6}*`}
                    {clickedUser.q7 && ` Q7: ${clickedUser.q7}*`}
                  </div>
                </>
              ) : (
                <div className="click-overall-score">
                  {clickedUser.totalScore}/5
                </div>
              )}
            </div>
            {clickedUser.reasoning && (
              <div className="click-reasoning">
                <h5>AI Analysis:</h5>
                <p>{clickedUser.reasoning}</p>
              </div>
            )}
            <div className="click-popup-body">
              {csvData && csvData[clickedUser.userNum - 1] && (
                <div className="click-user-data">
                  <h5>Application Details:</h5>
                  {Object.entries(csvData[clickedUser.userNum - 1]).slice(0, 5).map(([key, value]) => (
                    <div key={key} className="click-field">
                      <strong>{key}:</strong>
                      <div className="click-value">{value || 'N/A'}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        </>
      )}
    </div>
  );
}

export default App;
