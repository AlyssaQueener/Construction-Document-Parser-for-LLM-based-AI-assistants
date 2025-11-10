import { useState } from 'react';
import { Card, FileInput, Button, Select, Label, Alert, Spinner, Tabs, ThemeProvider } from 'flowbite-react';
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
    <ThemeProvider>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Construction Document Parser
            </h1>
            <p className="text-gray-600">
              Convert your construction documents into structured JSON
            </p>
          </div>

          <Tabs aria-label="Parser types" variant="underline">
            <Tabs.Item title="Floor Plans" active>
              <Card>
                <h5 className="text-2xl font-bold tracking-tight text-gray-900 mb-4">
                  Drawing Parser
                </h5>
                <p className="text-gray-700 mb-4">
                  Upload floor plans to extract title block information
                </p>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="floorplan-file" value="Upload Floor Plan Image" />
                    <FileInput
                      id="floorplan-file"
                      accept="image/*"
                      onChange={handleFileChange}
                    />
                  </div>

                  <Button
                    onClick={() => handleSubmit('/drawing_parser/')}
                    disabled={loading || !file}
                    className="w-full"
                  >
                    {loading ? <Spinner size="sm" className="mr-2" /> : null}
                    Parse Floor Plan
                  </Button>
                </div>
              </Card>
            </Tabs.Item>

            <Tabs.Item title="Gantt Charts">
              <Card>
                <h5 className="text-2xl font-bold tracking-tight text-gray-900 mb-4">
                  Program Parser
                </h5>
                <p className="text-gray-700 mb-4">
                  Upload Gantt charts to extract project schedule data
                </p>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="gantt-file" value="Upload Gantt Chart PDF" />
                    <FileInput
                      id="gantt-file"
                      accept="application/pdf"
                      onChange={handleFileChange}
                    />
                  </div>

                  <div>
                    <Label htmlFor="chart-format" value="Chart Format" />
                    <Select
                      id="chart-format"
                      value={chartFormat}
                      onChange={(e) => setChartFormat(e.target.value)}
                    >
                      <option value="visual">Visual (inferred from bars)</option>
                      <option value="tabular">Tabular (explicit dates)</option>
                    </Select>
                  </div>

                  <Button
                    onClick={() => handleSubmit('/gantt_parser/')}
                    disabled={loading || !file}
                    className="w-full"
                  >
                    {loading ? <Spinner size="sm" className="mr-2" /> : null}
                    Parse Gantt Chart
                  </Button>
                </div>
              </Card>
            </Tabs.Item>

            <Tabs.Item title="Bill of Quantities">
              <Card>
                <h5 className="text-2xl font-bold tracking-tight text-gray-900 mb-4">
                  Financial Parser
                </h5>
                <p className="text-gray-700 mb-4">
                  Upload Bill of Quantities to extract cost data
                </p>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="boq-file" value="Upload BOQ Document" />
                    <FileInput
                      id="boq-file"
                      accept="application/pdf,image/*"
                      onChange={handleFileChange}
                    />
                  </div>

                  <Button
                    onClick={() => handleSubmit('/financial_parser/')}
                    disabled={loading || !file}
                    className="w-full"
                  >
                    {loading ? <Spinner size="sm" className="mr-2" /> : null}
                    Parse BOQ
                  </Button>
                </div>
              </Card>
            </Tabs.Item>
          </Tabs>

          {error && (
            <Alert color="failure" className="mt-6">
              <span className="font-medium">Error!</span> {error}
            </Alert>
            )}

          {result && (
            <Card className="mt-6">
              <h5 className="text-2xl font-bold tracking-tight text-gray-900 mb-4">
                Results
              </h5>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Input Format</p>
                    <p className="text-lg text-gray-900">{result.input_format}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Extraction Status</p>
                    <p className="text-lg">
                      {result.is_extraction_succesful ? (
                        <span className="text-green-600 font-semibold">✓ Successful</span>
                      ) : (
                        <span className="text-red-600 font-semibold">✗ Failed</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Extraction Method</p>
                    <p className="text-lg text-gray-900">{result.extraction_method}</p>
                  </div>
                  {result.confident_value !== null && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Confidence</p>
                      <p className="text-lg text-gray-900">
                        {(result.confident_value * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Parsed Data</p>
                  <pre className="bg-gray-100 p-4 rounded-lg overflow-auto max-h-96 text-sm">
                    {JSON.stringify(result.result, null, 2)}
                  </pre>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;