import { useState } from 'react';
import { Card, Button, Select, Label, Alert, Spinner, Tabs } from 'flowbite-react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [chartFormat, setChartFormat] = useState('visual');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (endpoint) => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      let url = `http://localhost:8000${endpoint}`;
      if (endpoint.includes('gantt')) {
        url = `http://localhost:8000/gantt_parser/${chartFormat}`;
      }

      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing file');
    } finally {
      setLoading(false);
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
                    <span className="text-xs text-gray-600 mt-1">Images only</span>
                  </label>
                  <input
                    id="floorplan-file"
                    type="file"
                    accept="image/*"
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

                <Button
                  color="success"
                  size="lg"
                  onClick={() => handleSubmit('/drawing_parser/')}
                  disabled={loading || !file}
                  className="w-full"
                >
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

                <Button
                  color="success"
                  size="lg"
                  onClick={() => handleSubmit('/gantt_parser/')}
                  disabled={loading || !file}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Processing...
                    </>
                  ) : (
                    'Parse Gantt Chart'
                  )}
                </Button>
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

                <Button
                  color="success"
                  size="lg"
                  onClick={() => handleSubmit('/financial_parser/')}
                  disabled={loading || !file}
                  className="w-full"
                >
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
            </Card>
          </Tabs.Item>
        </Tabs>

        {/* Error Alert */}
        {error && (
          <Alert color="failure" className="mt-6 shadow-lg">
            <span className="font-bold text-lg">Error!</span> 
            <p className="mt-1">{error}</p>
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

      </div>

      {/* SIMPLE FOOTER - LOGO + FIND US */}
      <footer className="mt-2 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-8  max-w-6xl mx-auto">
        <div className="flex items-corner justify-corner gap-8">
          
          {/* Logo */}
          <div>
            <img 
              src="/logoTUM.png" 
              alt="tum Logo" 
              className="w-20.2 h-20"
            />
          </div>
          
          {/* Find us */}
          <div>
            <h3 className="font-bold text-lg mb-2 text-gray-900">Find us!</h3>
            <ul className="space-y-0.2">
              <li><a href="#" className="text-gray-700 hover:text-blue-600">Alyssa</a></li>
              <li><a href="#" className="text-gray-700 hover:text-blue-600">Bahar</a></li>
              <li><a href="#" className="text-gray-700 hover:text-blue-600">Rebekka</a></li>
            </ul>
          </div>

        </div>

  
      </footer>

    </div>
  );
}

export default App;