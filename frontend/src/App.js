import { Card, Button, Select, Label, Alert, Spinner, Tabs  } from 'flowbite-react';
import axios from 'axios';
import { useState, useEffect } from 'react';  

function App() {
  const [file, setFile] = useState(null);
  const [chartFormat, setChartFormat] = useState('visual');
  const [contentType, setContentType] = useState('titleblock-hybrid');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // AI Chatbot States
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

// Wake up the backend server on component mount
useEffect(() => {
  const wakeUpServer = async () => {
    try {
      await axios.get('https://construction-document-parser.onrender.com', {
        timeout: 30000
      });
    } catch (err) {
      console.log('Server wake-up call made:', err.message);
    }
  };
  
  wakeUpServer();
}, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
    setAiAnswer('');
  };

  const handleSubmit = async (endpoint) => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setAiAnswer('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      let url = `http://localhost:8000${endpoint}`;
      if (endpoint.includes('gantt')) {
        url = `https://construction-document-parser.onrender.com/gantt_parser/${chartFormat}`;
      }
      if (endpoint.includes('drawing')){
        url = `https://construction-document-parser.onrender.com/drawing_parser/${contentType}/`;  // ← WITH TRAILING SLASH
      }

      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
    } catch (err) {
      console.error('Full error:', err.response?.data);
      
      // Better error handling
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else if (Array.isArray(err.response.data.detail)) {
          const errorMessages = err.response.data.detail.map(e => e.msg).join(', ');
          setError(`Validation error: ${errorMessages}`);
        } else {
          setError('Error processing file');
        }
      } else {
        setError(err.message || 'Error processing file');
      }
    } finally {
      setLoading(false);
    }
  };
  const ganttInfo = {
    visual: {
      title: "Visual",
      desc: "Extracts tasks and timelines by interpreting the visual bar layout of the Gantt chart."
    },
    tabular: {
      title: "Tabular",
      desc: "Extracts schedule data from structured date tables within the chart."
    }
  };

  // AI Chatbot Function
  const askAI = async () => {
    if (!result || !aiQuestion.trim()) return;
    
    setAiLoading(true);
    setAiAnswer('');

    try {
      const response = await axios.post('https://construction-document-parser.onrender.com/ask_ai/', {
        question: aiQuestion,
        document_data: result.result
      });

      setAiAnswer(response.data.answer);
    } catch (err) {
      setAiAnswer('Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900 mb-3">
            Construction Document Parser
          </h1>
          <p className="text-lg text-gray-600">
            Convert your construction documents into structured JSON
          </p>
        </div>

        {/* Tabs */}
        <Tabs aria-label="Parser types">
          {/* FLOOR PLANS TAB */}
          <Tabs.Item title="Floor Plans" active>
            <Card className="shadow-xl">
              <h5 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">
                Drawing Parser
              </h5>
              <p className="text-gray-600 mb-6">
                Upload floor plans to extract title block information
              </p>

              <div className="space-y-6">
                <div className="flex items-center justify-center">
                  <label 
                    htmlFor="floorplan-file" 
                    className="w-40 h-40 flex flex-col items-center justify-center bg-gray-300 hover:bg-gray-400 rounded-2xl cursor-pointer transition-all shadow-lg hover:shadow-2xl"
                  >
                    <svg className="w-10 h-10 text-gray-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span className="text-base font-bold text-gray-700">Click to Upload</span>
                    <span className="text-xs text-gray-600 mt-1">
                    {contentType === 'rooms-deterministic' ? 'PDF only' : 'Images or PDF'}
                    </span>
                  </label>
                  <input
                    id="floorplan-file"
                    type="file"
                    accept={contentType === 'rooms-deterministic' ? 'application/pdf' : 'image/*,application/pdf'}
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                {file && (
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-gray-700">
                      Selected: <span className="font-semibold text-blue-600">{file.name}</span>
                    </p>
                  </div>
                )}

                <div>
                  <Label htmlFor="content-type" value="Content Type" className="text-lg mb-2" />
                  <Select
                    id="content-type"
                    value={contentType}
                    onChange={(e) => setContentType(e.target.value)}
                    className="text-lg"
                  >
                    <option value="titleblock-hybrid">Title Block</option>
                    <option value="rooms-deterministic">Rooms - Deterministic</option>
                    <option value="rooms-ai">Rooms - AI</option>
                    <option value="full-plan-ai">Full Plan - Hybrid</option>
                  </Select>
                </div>
                {/* Dynamic Info Box */}
                <div className="p-2 border border-gray-300 rounded-lg bg-white mt-3 text-sm">
    
                    {contentType === 'titleblock-hybrid' && (
                      <>
                        <span className="font-bold"> Title Block:</span> Extracts project metadata like project ID, architect, client, scale, and date from the title block section of floor plans.
                      </>
                    )}
                    {contentType === 'rooms-deterministic' && (
                      <>
                        <span className="font-bold"> Rooms - Deterministic:</span> Uses rule-based algorithms to identify room labels and calculate spatial relationships using Voronoi diagrams. Works best with clearly labeled room names best placed in the center of the rooms works also with more complex plans due to prefilterig.
                      </>
                    )}
                    {contentType === 'rooms-ai' && (
                      <>
                        <span className="font-bold"> Rooms - AI:</span> Uses AI vision models to intelligently detect room names, boundaries, and adjacencies. Struggles with complex plans.
                      </>
                    )}
                    {contentType === 'full-plan-ai' && (
                      <>
                        <span className="font-bold"> Full Plan:</span> Combined analysis extracting title block information and neigboring rooms hybrid and connected rooms with pure Ai based on neigbouring rooms.
                      </>
                    )}
                  
                </div>
              <div className="flex justify-center">
                <Button
                  color="success"
                  size="lg"
                  onClick={() => handleSubmit('/drawing_parser/')}
                  disabled={loading || !file}
                  className="
                    w-40 h-12                      // FIXED SIZE
                    border-2 border-gray-300
                    bg-gray-300 hover:bg-gray-400 
                    text-gray-800 textbase font-semibold 
                    rounded-lg 
                    flex items-center justify-center 
                    mx-auto
                  ">
                  {loading ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Processing...
                    </>
                  ) : (
                    'Parse Floor Plan'
                  )}
                </Button>
              </div>
              
              </div>
            </Card>
          </Tabs.Item>

          {/* GANTT CHARTS TAB */}
          <Tabs.Item title="Gantt Charts">
            <Card className="shadow-xl">
              <h5 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">
                Program Parser
              </h5>
              <p className="text-gray-600 mb-6">
                Upload Gantt charts to extract project schedule data
              </p>

              <div className="space-y-6">
                <div className="flex items-center justify-center">
                  <label 
                    htmlFor="gantt-file" 
                    className="w-40 h-40 flex flex-col items-center justify-center bg-gray-300 hover:bg-gray-400 rounded-2xl cursor-pointer transition-all shadow-lg hover:shadow-2xl"
                  >
                    <svg className="w-10 h-10 text-gray-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="text-base font-bold text-gray-700">Click to Upload</span>
                    <span className="text-xs text-gray-600 mt-1">PDF files only</span>
                  </label>
                  <input
                    id="gantt-file"
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                {file && (
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-gray-700">
                      Selected: <span className="font-semibold text-blue-600">{file.name}</span>
                    </p>
                  </div>
                )}

                <div>
                  <Label htmlFor="chart-format" value="Chart Format" className="text-lg mb-2" />
                  <Select
                    id="chart-format"
                    value={chartFormat}
                    onChange={(e) => setChartFormat(e.target.value)}
                    className="text-lg"
                  >
                    <option value="visual">Visual (inferred from bars)</option>
                    <option value="tabular">Tabular (explicit dates)</option>
                  </Select>
                </div>
                <div className="p-2 border border-gray-300 rounded-lg bg-white mt-3 text-sm">
                  <span className="font-bold">{ganttInfo[chartFormat].title}:</span>
                  {" "}
                  {ganttInfo[chartFormat].desc}
                </div>

               
              <div className="flex justify-center">
                <Button
                  color="success"
                  size="lg"
                  onClick={() => handleSubmit('/gantt_parser/')}
                  disabled={loading || !file}
                  className="
                    w-40 h-12                      // FIXED SIZE
                    border-2 border-gray-300 
                    bg-gray-300 hover:bg-gray-400 
                    text-gray-800 textbase font-semibold 
                    rounded-lg 
                    flex items-center justify-center 
                    mx-auto
                  ">                
                  {loading ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Processing...
                    </>
                  ) : (
                    'Parse Gantt-Chart'
                  )}
                </Button>
              </div>
              </div>
            </Card>
          </Tabs.Item>

          {/* BILL OF QUANTITIES TAB */}
          <Tabs.Item title="Bill of Quantities">
            <Card className="shadow-xl">
              <h5 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">
                Financial Parser
              </h5>
              <p className="text-gray-600 mb-6">
                Upload Bill of Quantities to extract cost data
              </p>

              <div className="space-y-6">
                <div className="flex items-center justify-center">
                  <label 
                    htmlFor="boq-file" 
                    className="w-40 h-40 flex flex-col items-center justify-center bg-gray-300 hover:bg-gray-400 rounded-2xl cursor-pointer transition-all shadow-lg hover:shadow-2xl"
                  >
                    <svg className="w-10 h-10 text-gray-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-base font-bold text-gray-700">Click to Upload</span>
                    <span className="text-xs text-gray-600 mt-1">PDF or Images</span>
                  </label>
                  <input
                    id="boq-file"
                    type="file"
                    accept="application/pdf,image/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                {file && (
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-gray-700">
                      Selected: <span className="font-semibold text-blue-600">{file.name}</span>
                    </p>
                  </div>
                )}
                <div className="p-2 border border-gray-300 rounded-lg bg-white mt-3 text-sm">
                  <span className="font-bold">{"Bill of Quantaties"}:</span>
                  {" "}
                  {"Extracts itemized cost data including quantities, unit prices, and total costs from Bills of Quantities documents used in construction projects."}
                </div>
              <div className="flex justify-center">
                <Button
                  color="success"
                  size="lg"
                  onClick={() => handleSubmit('/financial_parser/')}
                  disabled={loading || !file}
                  className="
                    w-40 h-12                      // FIXED SIZE
                    border-2 border-gray-300 
                    bg-gray-300 hover:bg-gray-400 
                    text-gray-800 textbase font-semibold 
                    rounded-lg 
                    flex items-center justify-center 
                    mx-auto
                  ">
                  {loading ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Processing...
                    </>
                  ) : (
                    'Parse BOQ'
                  )}
                </Button>
              </div>
              
              </div>
            </Card>
          </Tabs.Item>
        </Tabs>

        {/* Error Alert - IMPROVED */}
        {error && (
          <Alert color="failure" className="mt-6 shadow-lg">
            <span className="font-bold text-lg">Error!</span> 
            <p className="mt-1">
              {typeof error === 'string' ? error : 'An error occurred while processing your file'}
            </p>
            {typeof error === 'object' && (
              <details className="mt-2">
                <summary className="cursor-pointer text-sm">Show details</summary>
                <pre className="mt-2 text-xs bg-red-900 text-white p-2 rounded overflow-auto max-h-40">
                  {JSON.stringify(error, null, 2)}
                </pre>
              </details>
            )}
          </Alert>
        )}

        {/* Results Display */}
        {result && (
          <Card className="mt-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h5 className="text-3xl font-bold tracking-tight text-gray-900">
                Results
              </h5>
              {result.is_extraction_succesful && (
                <span className="text-2xl text-green-600 font-bold">✓ Success</span>
              )}
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-medium text-gray-500 mb-1">Input Format</p>
                  <p className="text-xl font-semibold text-gray-900">{result.input_format}</p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-medium text-gray-500 mb-1">Extraction Status</p>
                  <p className="text-xl font-semibold">
                    {result.is_extraction_succesful ? (
                      <span className="text-green-600">Successful</span>
                    ) : (
                      <span className="text-red-600">Failed</span>
                    )}
                  </p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-medium text-gray-500 mb-1">Extraction Method</p>
                  <p className="text-xl font-semibold text-gray-900">{result.extraction_method}</p>
                </div>
                
                {result.confident_value !== null && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-500 mb-1">Confidence</p>
                    <p className="text-xl font-semibold text-blue-600">
                      {(result.confident_value * 100).toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-lg font-semibold text-gray-700">Parsed Data (JSON)</p>
                  <Button 
                    size="xs" 
                    color="light"
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(result.result, null, 2));
                      alert('JSON copied to clipboard!');
                    }}
                  >
                    Copy JSON
                  </Button>
                </div>
                <pre className="bg-gray-900 text-green-400 p-6 rounded-lg overflow-auto max-h-96 text-sm font-mono shadow-inner">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </div>
            </div>
          </Card>
        )}

        {/* AI CHATBOT */}
        {result && (
          <Card className="mt-6 shadow-2xl">
            <h5 className="text-2xl font-bold text-gray-900 mb-2">
              Ask AI About This Document
            </h5>
            <p className="text-gray-600 mb-4">
              Ask questions about the parsed construction data
            </p>

            {/* Question Input */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                placeholder="e.g., What is the project location?"
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && !aiLoading && askAI()}
                disabled={aiLoading}
              />
              <Button 
                onClick={askAI} 
                color="black"
                size="lg"
                disabled={aiLoading || !aiQuestion.trim()}
              >
                {aiLoading ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Asking...
                  </>
                ) : (
                  'Ask AI'
                )}
              </Button>
            </div>

            {/* Answer Display */}
            {aiAnswer && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="font-semibold text-blue-900 mb-2">Answer:</p>
                <p className="text-gray-800 whitespace-pre-wrap">{aiAnswer}</p>
              </div>
            )}

            {/* Example Questions */}
            {!aiAnswer && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">💡 Try these questions:</p>
                <div className="flex flex-wrap gap-2">
                  <button 
                    onClick={() => setAiQuestion('What is the project ID and location?')}
                    className="text-xs bg-gray-200 px-3 py-1 rounded-full hover:bg-gray-300 transition"
                    disabled={aiLoading}
                  >
                    What is the project ID and location?
                  </button>
                  <button 
                    onClick={() => setAiQuestion('Who is the client and architect?')}
                    className="text-xs bg-gray-200 px-3 py-1 rounded-full hover:bg-gray-300 transition"
                    disabled={aiLoading}
                  >
                    Who is the client and architect?
                  </button>
                  <button 
                    onClick={() => setAiQuestion('What is the plan scale and format?')}
                    className="text-xs bg-gray-200 px-3 py-1 rounded-full hover:bg-gray-300 transition"
                    disabled={aiLoading}
                  >
                    What is the plan scale and format?
                  </button>
                  <button 
                    onClick={() => setAiQuestion('Summarize the key information')}
                    className="text-xs bg-gray-200 px-3 py-1 rounded-full hover:bg-gray-300 transition"
                    disabled={aiLoading}
                  >
                    Summarize the key information
                  </button>
                </div>
              </div>
            )}
          </Card>
        )}

      </div>

      {/* FOOTER */}
      <footer className="mt-16 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-8 max-w-6xl mx-auto">
        <div className="flex items-corner justify-corner gap-8">
          
          {/* Logo */}
          <div>
            <img 
              src="/logotum.png" 
              alt="TUM Logo" 
              className="w-34 h-20"
            />
          </div>
          
          {/* Find us */}
          <div>
            <h3 className="font-bold text-lg mb-2 text-gray-900">Find us!</h3>
            <ul className="space-y-1">
              <li><a href="https://www.linkedin.com/in/alyssa-queener-8932b2318?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BfReaJrcdQb%2BuvLYnrqWlng%3D%3D" className="text-gray-700 hover:text-blue-600">Alyssa</a></li>
              <li><a href="https://www.linkedin.com/in/bahar-moradi-b21969190?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BRYdfj5hATpSZ5jil3zmsqQ%3D%3D" className="text-gray-700 hover:text-blue-600">Bahar</a></li>
              <li><a href="https://www.linkedin.com/in/rebekka-buter-4532b926b?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BLV4gW%2FZfRaiBv%2BcF3fLhJw%3D%3D" className="text-gray-700 hover:text-blue-600">Rebekka</a></li>
            </ul>
          </div>

        </div>

        {/* Copyright */}
        <div className="border-t border-gray-300 mt-8 pt-6 text-center text-gray-600">
          © 2024 Construction Document Parser™. All rights reserved.
        </div>
      </footer>

    </div>
  );
}

export default App;