import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Tabs,
  Tab
} from '@mui/material';
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import api from '../services/api';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function AdvancedFeatures() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Portfolio optimization state
  const [portfolioData, setPortfolioData] = useState(null);
  const [efficientFrontier, setEfficientFrontier] = useState(null);
  const [optimizationMethod, setOptimizationMethod] = useState('max_sharpe');
  const [portfolioReturnsInput, setPortfolioReturnsInput] = useState('[[0.01,0.005,-0.002,0.007],[0.008,0.004,-0.001,0.006],[0.012,0.002,-0.003,0.005]]');
  
  // Risk analysis state
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [riskReturnsInput, setRiskReturnsInput] = useState('[0.01,-0.003,0.007,0.002,-0.001,0.004]');
  
  // Position sizing state
  const [positionSize, setPositionSize] = useState(null);
  const [stopLoss, setStopLoss] = useState(null);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError('');
  };

  const parseJsonInput = (value, label) => {
    try {
      return JSON.parse(value);
    } catch (err) {
      throw new Error(`${label} must be valid JSON`);
    }
  };
  
  const optimizePortfolio = async () => {
    setLoading(true);
    setError('');
    
    try {
      const returns = parseJsonInput(portfolioReturnsInput, 'Portfolio returns');
      if (!Array.isArray(returns) || returns.length === 0 || !Array.isArray(returns[0])) {
        throw new Error('Portfolio returns must be a 2D JSON array');
      }
      
      const response = await api.post('/api/advanced/portfolio/optimize', {
        returns,
        method: optimizationMethod,
        risk_free_rate: 0.02
      });
      
      setPortfolioData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Portfolio optimization failed');
    } finally {
      setLoading(false);
    }
  };
  
  const calculateEfficientFrontier = async () => {
    setLoading(true);
    setError('');
    
    try {
      const returns = parseJsonInput(portfolioReturnsInput, 'Portfolio returns');
      if (!Array.isArray(returns) || returns.length === 0 || !Array.isArray(returns[0])) {
        throw new Error('Portfolio returns must be a 2D JSON array');
      }
      
      const response = await api.post('/api/advanced/portfolio/efficient-frontier?n_points=30', {
        returns,
        risk_free_rate: 0.02
      });
      
      setEfficientFrontier(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Efficient frontier calculation failed');
    } finally {
      setLoading(false);
    }
  };
  
  const analyzeRisk = async () => {
    setLoading(true);
    setError('');
    
    try {
      const returns = parseJsonInput(riskReturnsInput, 'Risk returns');
      if (!Array.isArray(returns) || returns.length === 0) {
        throw new Error('Risk returns must be a non-empty JSON array');
      }
      const equityCurve = returns.reduce((acc, r) => {
        const last = acc[acc.length - 1] || 1.0;
        acc.push(last * (1 + r));
        return acc;
      }, [1.0]);
      
      const response = await api.post('/api/advanced/risk/analyze', {
        returns,
        equity_curve: equityCurve,
        risk_free_rate: 0.02
      });
      
      setRiskMetrics(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Risk analysis failed');
    } finally {
      setLoading(false);
    }
  };
  
  const calculatePositionSize = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/advanced/risk/position-size?initial_capital=100000', {
        symbol: 'AAPL',
        signal_strength: 0.75,
        current_price: 150.0,
        volatility: 0.25,
        method: 'volatility'
      });
      
      setPositionSize(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Position sizing failed');
    } finally {
      setLoading(false);
    }
  };
  
  const calculateStopLoss = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/advanced/risk/stop-loss?risk_reward_ratio=2.5', {
        entry_price: 150.0,
        volatility: 0.25,
        atr: 3.5,
        method: 'atr'
      });
      
      setStopLoss(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Stop-loss calculation failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Advanced Features
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Portfolio Optimization" />
          <Tab label="Risk Analytics" />
          <Tab label="Risk Management" />
        </Tabs>
        
        {/* Portfolio Optimization Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Optimize Portfolio
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Optimization Method</InputLabel>
                  <Select
                    value={optimizationMethod}
                    onChange={(e) => setOptimizationMethod(e.target.value)}
                    label="Optimization Method"
                  >
                    <MenuItem value="max_sharpe">Maximum Sharpe Ratio</MenuItem>
                    <MenuItem value="min_variance">Minimum Variance</MenuItem>
                    <MenuItem value="risk_parity">Risk Parity</MenuItem>
                    <MenuItem value="max_return">Maximum Return</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  label="Portfolio Returns (JSON 2D array)"
                  value={portfolioReturnsInput}
                  onChange={(e) => setPortfolioReturnsInput(e.target.value)}
                  fullWidth
                  multiline
                  minRows={4}
                  sx={{ mb: 2 }}
                />
                
                <Button
                  variant="contained"
                  fullWidth
                  onClick={optimizePortfolio}
                  disabled={loading}
                  sx={{ mb: 2 }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Optimize'}
                </Button>
                
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={calculateEfficientFrontier}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Calculate Efficient Frontier'}
                </Button>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={8}>
              {portfolioData && (
                <Paper elevation={2} sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Optimization Results
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Expected Return
                          </Typography>
                          <Typography variant="h5">
                            {(portfolioData.expected_return * 100).toFixed(2)}%
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    
                    <Grid item xs={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Volatility
                          </Typography>
                          <Typography variant="h5">
                            {(portfolioData.volatility * 100).toFixed(2)}%
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    
                    <Grid item xs={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Sharpe Ratio
                          </Typography>
                          <Typography variant="h5">
                            {portfolioData.sharpe_ratio.toFixed(3)}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    
                    <Grid item xs={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Diversification
                          </Typography>
                          <Typography variant="h5">
                            {portfolioData.diversification_ratio.toFixed(2)}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                        Portfolio Weights
                      </Typography>
                      {portfolioData.weights.map((weight, idx) => (
                        <Box key={idx} sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Asset {idx + 1}: {(weight * 100).toFixed(2)}%
                          </Typography>
                          <Box
                            sx={{
                              width: '100%',
                              height: 8,
                              bgcolor: 'grey.300',
                              borderRadius: 1,
                              overflow: 'hidden'
                            }}
                          >
                            <Box
                              sx={{
                                width: `${weight * 100}%`,
                                height: '100%',
                                bgcolor: 'primary.main'
                              }}
                            />
                          </Box>
                        </Box>
                      ))}
                    </Grid>
                  </Grid>
                </Paper>
              )}
              
              {efficientFrontier && (
                <Paper elevation={2} sx={{ p: 2, mt: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Efficient Frontier
                  </Typography>
                  
                  <ResponsiveContainer width="100%" height={400}>
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        dataKey="volatility"
                        name="Volatility"
                        label={{ value: 'Volatility (%)', position: 'bottom' }}
                        tickFormatter={(val) => (val * 100).toFixed(1)}
                      />
                      <YAxis
                        type="number"
                        dataKey="return"
                        name="Return"
                        label={{ value: 'Expected Return (%)', angle: -90, position: 'left' }}
                        tickFormatter={(val) => (val * 100).toFixed(1)}
                      />
                      <Tooltip
                        formatter={(value) => (value * 100).toFixed(2) + '%'}
                      />
                      <Legend />
                      <Scatter
                        name="Efficient Frontier"
                        data={efficientFrontier.frontier}
                        fill="#8884d8"
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </Paper>
              )}
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Risk Analytics Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Analyze Risk
                </Typography>
                
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Calculate comprehensive risk metrics including VaR, CVaR, Sharpe ratio, and drawdown statistics.
                </Typography>

                <TextField
                  label="Returns Series (JSON array)"
                  value={riskReturnsInput}
                  onChange={(e) => setRiskReturnsInput(e.target.value)}
                  fullWidth
                  multiline
                  minRows={4}
                  sx={{ mb: 2 }}
                />
                
                <Button
                  variant="contained"
                  fullWidth
                  onClick={analyzeRisk}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Analyze Risk'}
                </Button>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={8}>
              {riskMetrics && (
                <Paper elevation={2} sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Risk Metrics
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="subtitle1" gutterBottom sx={{ mt: 1 }}>
                        Risk-Adjusted Returns
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={4}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                Sharpe Ratio
                              </Typography>
                              <Typography variant="h6">
                                {riskMetrics.metrics.risk_adjusted_returns.sharpe_ratio}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                        <Grid item xs={4}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                Sortino Ratio
                              </Typography>
                              <Typography variant="h6">
                                {riskMetrics.metrics.risk_adjusted_returns.sortino_ratio}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                        <Grid item xs={4}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                Calmar Ratio
                              </Typography>
                              <Typography variant="h6">
                                {riskMetrics.metrics.risk_adjusted_returns.calmar_ratio}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      </Grid>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Typography variant="subtitle1" gutterBottom sx={{ mt: 1 }}>
                        Value at Risk (VaR)
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                VaR 95%
                              </Typography>
                              <Typography variant="h6" color="error">
                                {riskMetrics.metrics.value_at_risk.var_95}%
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                        <Grid item xs={6}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                CVaR 95%
                              </Typography>
                              <Typography variant="h6" color="error">
                                {riskMetrics.metrics.value_at_risk.cvar_95}%
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      </Grid>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Typography variant="subtitle1" gutterBottom sx={{ mt: 1 }}>
                        Drawdown
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                Max Drawdown
                              </Typography>
                              <Typography variant="h6" color="error">
                                {riskMetrics.metrics.drawdown.max_drawdown}%
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                        <Grid item xs={6}>
                          <Card>
                            <CardContent>
                              <Typography color="textSecondary" variant="body2">
                                Max DD Duration
                              </Typography>
                              <Typography variant="h6">
                                {riskMetrics.metrics.drawdown.max_drawdown_duration_days} days
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      </Grid>
                    </Grid>
                  </Grid>
                </Paper>
              )}
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Risk Management Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Position Sizing
                </Typography>
                
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Calculate optimal position size based on volatility
                </Typography>
                
                <Button
                  variant="contained"
                  fullWidth
                  onClick={calculatePositionSize}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Calculate Position Size'}
                </Button>
                
                {positionSize && (
                  <Box sx={{ mt: 3 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="body2">
                              Position Size
                            </Typography>
                            <Typography variant="h6">
                              {positionSize.position_size.toFixed(0)} shares
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="body2">
                              Position Value
                            </Typography>
                            <Typography variant="h6">
                              ${positionSize.position_value.toFixed(0)}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="body2">
                              Portfolio %
                            </Typography>
                            <Typography variant="h6">
                              {(positionSize.position_pct * 100).toFixed(2)}%
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Stop-Loss / Take-Profit
                </Typography>
                
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Calculate stop-loss and take-profit levels based on ATR
                </Typography>
                
                <Button
                  variant="contained"
                  fullWidth
                  onClick={calculateStopLoss}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Calculate Levels'}
                </Button>
                
                {stopLoss && (
                  <Box sx={{ mt: 3 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="body2">
                              Entry Price
                            </Typography>
                            <Typography variant="h6">
                              ${stopLoss.entry_price.toFixed(2)}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card sx={{ bgcolor: 'error.light' }}>
                          <CardContent>
                            <Typography color="white" variant="body2">
                              Stop-Loss
                            </Typography>
                            <Typography variant="h6" color="white">
                              ${stopLoss.stop_loss.toFixed(2)}
                            </Typography>
                            <Typography variant="caption" color="white">
                              Risk: {(stopLoss.risk_pct * 100).toFixed(2)}%
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card sx={{ bgcolor: 'success.light' }}>
                          <CardContent>
                            <Typography color="white" variant="body2">
                              Take-Profit
                            </Typography>
                            <Typography variant="h6" color="white">
                              ${stopLoss.take_profit.toFixed(2)}
                            </Typography>
                            <Typography variant="caption" color="white">
                              Reward: {(stopLoss.reward_pct * 100).toFixed(2)}%
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="body2">
                              Risk/Reward Ratio
                            </Typography>
                            <Typography variant="h6">
                              1 : {stopLoss.risk_reward_ratio.toFixed(2)}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
}
