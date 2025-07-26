import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Skeleton } from './ui/skeleton';
import { Progress } from './ui/progress';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Area, AreaChart
} from 'recharts';
import { 
  Server, HardDrive, Database, Zap, Cloud, TrendingDown, 
  DollarSign, AlertTriangle, Filter, Search, ChevronLeft, 
  ChevronRight, Eye, Download, RefreshCw, Calendar, Settings,
  BarChart3, PieChart as PieChartIcon, Activity, Shield,
  Lightbulb, Target, Users, Globe, Menu, TrendingUp
} from 'lucide-react';
import RecommendationCard from './RecommendationCard';
import fetchRecommendations from '../api/fetchRecommendations';

const ITEMS_PER_PAGE = 12;

const COLORS = {
  ec2: '#FF6B6B',
  ebs: '#4ECDC4', 
  s3: '#45B7D1',
  rds: '#96CEB4',
  lambda: '#FFEAA7',
  default: '#DDA0DD'
};

function Dashboard() {
  const [recommendations, setRecommendations] = useState([]);
  const [filteredRecommendations, setFilteredRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTab, setActiveTab] = useState('insights');
  const [filters, setFilters] = useState({
    resourceType: 'all',
    region: 'all',
    search: ''
  });

  // Stats
  const [stats, setStats] = useState({
    totalResources: 537,
    totalSavings: 45240,
    byType: [
      { name: 'EC2', value: 18500, count: 125 },
      { name: 'RDS', value: 12400, count: 45 },
      { name: 'S3', value: 8200, count: 89 },
      { name: 'EBS', value: 4140, count: 67 },
      { name: 'LAMBDA', value: 2000, count: 211 }
    ],
    byRegion: [
      { name: 'us-east-1', value: 18500, count: 125 },
      { name: 'us-west-2', value: 12400, count: 98 },
      { name: 'eu-west-1', value: 8200, count: 76 },
      { name: 'ap-south-1', value: 6140, count: 238 }
    ],
    costTrend: [
      { month: 'Jan', savings: 31668, potential: 35240 },
      { month: 'Feb', savings: 36192, potential: 38604 },
      { month: 'Mar', savings: 40716, potential: 42978 },
      { month: 'Apr', savings: 45240, potential: 49764 }
    ]
  });

  useEffect(() => {
    loadRecommendations();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [recommendations, filters]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      // Simulate API call
      setTimeout(() => {
        const mockData = [
          {
            resourceId: 'i-0123456789abcdef0',
            resourceName: 'web-server-1',
            resourceType: 'ec2',
            region: 'us-east-1',
            reason: 'Instance running with low CPU utilization',
            cost_impact: 245
          },
          {
            resourceId: 'vol-0987654321fedcba0',
            resourceName: 'data-volume',
            resourceType: 'ebs',
            region: 'us-west-2',
            reason: 'Unattached EBS volume',
            cost_impact: 120
          }
        ];
        setRecommendations(mockData);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...recommendations];

    if (filters.resourceType !== 'all') {
      filtered = filtered.filter(item => item.resourceType === filters.resourceType);
    }

    if (filters.region !== 'all') {
      filtered = filtered.filter(item => (item.region || 'unknown') === filters.region);
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(item => 
        item.resourceName?.toLowerCase().includes(searchLower) ||
        item.resourceId?.toLowerCase().includes(searchLower) ||
        item.reason?.toLowerCase().includes(searchLower)
      );
    }

    setFilteredRecommendations(filtered);
    setCurrentPage(1);
  };

  const getResourceIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'ec2': return <Server className="w-4 h-4" />;
      case 'ebs': return <HardDrive className="w-4 h-4" />;
      case 's3': return <Database className="w-4 h-4" />;
      case 'rds': return <Database className="w-4 h-4" />;
      case 'lambda': return <Zap className="w-4 h-4" />;
      default: return <Cloud className="w-4 h-4" />;
    }
  };

  const uniqueTypes = [...new Set(recommendations.map(item => item.resourceType))];
  const uniqueRegions = [...new Set(recommendations.map(item => item.region || 'unknown'))];

  const paginatedData = filteredRecommendations.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const totalPages = Math.ceil(filteredRecommendations.length / ITEMS_PER_PAGE);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Modern Sidebar */}
      <div className="w-64 bg-white shadow-lg border-r border-gray-100">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2.5 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Cloud Intelligence</h1>
              <p className="text-xs text-gray-500 mt-0.5">AI-Powered Insights</p>
            </div>
          </div>
        </div>
        
        <nav className="px-4">
          <div className="space-y-2">
            <button
              onClick={() => setActiveTab('insights')}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left rounded-xl text-sm font-medium transition-all duration-200 ${
                activeTab === 'insights'
                  ? 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 shadow-sm border border-blue-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <div className={`p-1 rounded-lg ${
                activeTab === 'insights' ? 'bg-blue-200' : 'bg-gray-100'
              }`}>
                <BarChart3 className="w-4 h-4" />
              </div>
              Insights
            </button>
            
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left rounded-xl text-sm font-medium transition-all duration-200 ${
                activeTab === 'recommendations'
                  ? 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 shadow-sm border border-blue-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <div className={`p-1 rounded-lg ${
                activeTab === 'recommendations' ? 'bg-blue-200' : 'bg-gray-100'
              }`}>
                <Lightbulb className="w-4 h-4" />
              </div>
              Recommendations
            </button>
          </div>
        </nav>

        {/* Sidebar Footer */}
        <div className="absolute bottom-6 left-4 right-4">
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">AI</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">AI Assistant</p>
                <p className="text-xs text-gray-500">Online & Ready</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {activeTab === 'insights' ? (
            <InsightsContent 
              stats={stats} 
              loadRecommendations={loadRecommendations}
              recommendations={recommendations}
            />
          ) : (
            <RecommendationsContent 
              recommendations={recommendations}
              filteredRecommendations={filteredRecommendations}
              filters={filters}
              setFilters={setFilters}
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              paginatedData={paginatedData}
              totalPages={totalPages}
              getResourceIcon={getResourceIcon}
              uniqueTypes={uniqueTypes}
              uniqueRegions={uniqueRegions}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Enhanced Insights Content Component
function InsightsContent({ stats, loadRecommendations, recommendations }) {
  return (
    <div className="space-y-8">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Insights
          </h1>
          <p className="text-gray-600 text-base">
            Optimize your cloud spend with AI-powered insights
          </p>
        </div>
        <Button 
          onClick={loadRecommendations} 
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Enhanced Stats Cards */}
      <div className="grid grid-cols-4 gap-6">
        {/* Card 1 - Total Resources */}
        <Card className="bg-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 mb-2">537</p>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">TOTAL RESOURCES</p>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 px-2 py-1 bg-orange-50 rounded-full">
                    <AlertTriangle className="w-3 h-3 text-orange-500" />
                    <span className="text-xs text-orange-700 font-medium">Wasteful detected</span>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl">
                <AlertTriangle className="w-8 h-8 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 2 - Monthly Savings */}
        <Card className="bg-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 mb-2">$45,240</p>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">MONTHLY SAVINGS</p>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 px-2 py-1 bg-green-50 rounded-full">
                    <TrendingUp className="w-3 h-3 text-green-500" />
                    <span className="text-xs text-green-700 font-medium">+18% vs last month</span>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl">
                <DollarSign className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 3 - Service Types */}
        <Card className="bg-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 mb-2">6</p>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">SERVICE TYPES</p>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 px-2 py-1 bg-blue-50 rounded-full">
                    <Cloud className="w-3 h-3 text-blue-500" />
                    <span className="text-xs text-blue-700 font-medium">AWS services analyzed</span>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl">
                <Server className="w-8 h-8 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 4 - Avg Impact */}
        <Card className="bg-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 mb-2">$84</p>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">AVG. IMPACT</p>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 px-2 py-1 bg-purple-50 rounded-full">
                    <Activity className="w-3 h-3 text-purple-500" />
                    <span className="text-xs text-purple-700 font-medium">Per resource savings</span>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl">
                <TrendingDown className="w-8 h-8 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Charts */}
      <div className="grid grid-cols-2 gap-8">
        {/* Cost Impact Analysis Chart */}
        <Card className="bg-white border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardHeader className="pb-4 px-6 pt-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-gray-900">
                  Cost Impact Analysis
                </CardTitle>
                <CardDescription className="text-sm text-gray-600 mt-1">
                  Monthly savings potential across AWS services
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-6">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={stats.byType} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis 
                  dataKey="name" 
                  stroke="#64748b"
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  axisLine={{ stroke: '#e2e8f0' }}
                />
                <YAxis 
                  stroke="#64748b"
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  axisLine={{ stroke: '#e2e8f0' }}
                />
                <Tooltip 
                  formatter={(value) => [`$${value.toLocaleString()}`, 'Monthly Savings']}
                  labelFormatter={(label) => `Service: ${label}`}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar 
                  dataKey="value" 
                  fill="url(#colorGradient)" 
                  radius={[6, 6, 0, 0]}
                />
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" />
                    <stop offset="100%" stopColor="#1D4ED8" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Regional Impact Chart */}
        <Card className="bg-white border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardHeader className="pb-4 px-6 pt-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg">
                <Globe className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-gray-900">
                  Regional Impact
                </CardTitle>
                <CardDescription className="text-sm text-gray-600 mt-1">
                  Resources distribution by region
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-6">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={stats.byRegion}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => percent > 8 ? `${name} ${(percent * 100).toFixed(0)}%` : ''}
                  outerRadius={90}
                  fill="#8884d8"
                  dataKey="value"
                  stroke="#fff"
                  strokeWidth={3}
                >
                  {stats.byRegion.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={Object.values(COLORS)[index % Object.values(COLORS).length]} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [`$${value.toLocaleString()}`, 'Monthly Savings']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            
            {/* Enhanced Legend */}
            <div className="mt-6 space-y-3">
              {stats.byRegion.slice(0, 4).map((region, index) => (
                <div key={region.name} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-4 h-4 rounded-full shadow-sm" 
                      style={{ backgroundColor: Object.values(COLORS)[index % Object.values(COLORS).length] }}
                    ></div>
                    <span className="text-sm font-medium text-gray-700">{region.name}</span>
                    <Badge variant="outline" className="text-xs px-2 py-0.5">
                      {region.count} resources
                    </Badge>
                  </div>
                  <span className="font-bold text-gray-900">
                    ${region.value.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Keep the RecommendationsContent component the same as before but with enhanced styling
function RecommendationsContent({ 
  recommendations, 
  filteredRecommendations, 
  filters, 
  setFilters, 
  currentPage, 
  setCurrentPage, 
  paginatedData, 
  totalPages,
  getResourceIcon,
  uniqueTypes,
  uniqueRegions
}) {
  return (
    <div className="space-y-8">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Recommendations
          </h1>
          <p className="text-gray-600 text-base">
            AI-powered optimization recommendations for your cloud resources
          </p>
        </div>
      </div>

      {/* Enhanced Filters Section */}
      <Card className="bg-white border-0 shadow-lg rounded-2xl overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                <Filter className="w-5 h-5 text-blue-600" />
              </div>
              <span className="font-bold text-gray-900 text-lg">Smart Filters</span>
            </div>
            
            <div className="flex flex-wrap gap-4 flex-1">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                <Input
                  placeholder="Search resources, IDs, or reasons..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10 w-80 bg-white border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <Select
                value={filters.resourceType}
                onValueChange={(value) => setFilters(prev => ({ ...prev, resourceType: value }))}
              >
                <SelectTrigger className="w-48 bg-white border-gray-200 rounded-xl">
                  <SelectValue placeholder="Service Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Services</SelectItem>
                  {uniqueTypes.map(type => (
                    <SelectItem key={type} value={type}>
                      <div className="flex items-center gap-2">
                        {getResourceIcon(type)}
                        {type.toUpperCase()}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={filters.region}
                onValueChange={(value) => setFilters(prev => ({ ...prev, region: value }))}
              >
                <SelectTrigger className="w-48 bg-white border-gray-200 rounded-xl">
                  <SelectValue placeholder="Region" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Regions</SelectItem>
                  {uniqueRegions.map(region => (
                    <SelectItem key={region} value={region}>
                      {region}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-3">
              <Badge className="text-sm px-4 py-2 bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border-blue-200 rounded-xl">
                {filteredRecommendations.length} result{filteredRecommendations.length !== 1 ? 's' : ''}
              </Badge>
              {(filters.search || filters.resourceType !== 'all' || filters.region !== 'all') && (
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setFilters({ resourceType: 'all', region: 'all', search: '' })}
                  className="text-gray-500 hover:text-gray-700 rounded-xl"
                >
                  Clear filters
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rest of the content with enhanced styling */}
      {filteredRecommendations.length === 0 ? (
        <Card className="bg-white border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardContent className="py-20 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-24 h-24 bg-gradient-to-br from-gray-50 to-gray-100 rounded-full flex items-center justify-center mx-auto mb-8 shadow-lg">
                {filters.search || filters.resourceType !== 'all' || filters.region !== 'all' ? (
                  <Search className="w-12 h-12 text-gray-400" />
                ) : (
                  <Shield className="w-12 h-12 text-green-500" />
                )}
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                {filters.search || filters.resourceType !== 'all' || filters.region !== 'all' 
                  ? 'No matching resources found'
                  : 'All systems optimized! 🎉'}
              </h3>
              <p className="text-gray-600 leading-relaxed text-lg">
                {filters.search || filters.resourceType !== 'all' || filters.region !== 'all' 
                  ? 'Try adjusting your filters or search terms to discover more optimization opportunities.'
                  : 'Congratulations! No wasteful resources detected in your current infrastructure.'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold text-gray-900">
                Optimization Opportunities
              </h2>
              <Badge className="bg-gradient-to-r from-amber-50 to-amber-100 text-amber-800 px-4 py-2 rounded-xl border border-amber-200">
                <Lightbulb className="w-4 h-4 mr-2" />
                {filteredRecommendations.length} opportunities
              </Badge>
            </div>
            
            <span className="text-sm text-gray-500 bg-gray-50 px-3 py-1 rounded-lg">
              Page {currentPage} of {totalPages}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {paginatedData.map((resource, index) => (
              <RecommendationCard key={resource.resourceId || index} resource={resource} />
            ))}
          </div>

          {totalPages > 1 && (
            <Card className="bg-white border-0 shadow-lg rounded-2xl overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1} to{' '}
                    {Math.min(currentPage * ITEMS_PER_PAGE, filteredRecommendations.length)} of{' '}
                    {filteredRecommendations.length} results
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="rounded-xl border-gray-200 hover:bg-gray-50"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </Button>
                    
                    <div className="flex items-center gap-1">
                      {[...Array(Math.min(5, totalPages))].map((_, i) => {
                        const page = i + 1;
                        if (totalPages <= 5) {
                          return (
                            <Button
                              key={page}
                              variant={currentPage === page ? "default" : "outline"}
                              size="sm"
                              onClick={() => setCurrentPage(page)}
                              className={`w-10 h-10 rounded-xl ${
                                currentPage === page 
                                  ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                                  : 'border-gray-200 hover:bg-gray-50'
                              }`}
                            >
                              {page}
                            </Button>
                          );
                        }
                        return null;
                      })}
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="rounded-xl border-gray-200 hover:bg-gray-50"
                    >
                      Next
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="flex h-screen bg-gray-50">
      <div className="w-64 bg-white shadow-lg border-r border-gray-100">
        <div className="p-6">
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
        <div className="px-6 space-y-3">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-8">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-96" />
            </div>
            <Skeleton className="h-10 w-24 rounded-xl" />
          </div>
          
          <div className="grid grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-36 w-full rounded-2xl" />
            ))}
          </div>
          
          <div className="grid grid-cols-2 gap-8">
            <Skeleton className="h-96 w-full rounded-2xl" />
            <Skeleton className="h-96 w-full rounded-2xl" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;