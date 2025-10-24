import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { Building2, DollarSign, FileText, Edit, Download, Users, Calendar, Shield, Loader2 } from "lucide-react";
import { api } from "../lib/apiClient";

const DynamicTermSheet = ({ termSheetData, onEdit }) => {
  const [generatedTermSheet, setGeneratedTermSheet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (termSheetData) {
      generateTermSheet();
    }
  }, [termSheetData]);

  const generateTermSheet = async () => {
    if (!termSheetData) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/api/copilot/generate-term-sheet', termSheetData);
      if (response.data.status === 'success') {
        setGeneratedTermSheet(response.data.term_sheet);
      } else {
        setError(response.data.message || 'Failed to generate term sheet');
      }
    } catch (err) {
      console.error('Term sheet generation error:', err);
      setError(err.message || 'Failed to generate term sheet');
    } finally {
      setLoading(false);
    }
  };

  if (!termSheetData) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500">
        <div className="text-center">
          <FileText className="w-12 h-12 mx-auto mb-4 text-zinc-400" />
          <p>No term sheet data available</p>
          <p className="text-sm">Complete the information collection to generate a term sheet</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500">
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 text-indigo-600 animate-spin" />
          <p>Generating term sheet...</p>
          <p className="text-sm">This may take a moment</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500">
        <div className="text-center">
          <FileText className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-red-600">Error generating term sheet</p>
          <p className="text-sm text-red-500">{error}</p>
          <Button 
            onClick={generateTermSheet}
            className="mt-4 bg-indigo-600 hover:bg-indigo-700"
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  const { company, investors, deal, terms } = termSheetData;

  // Helper function to format currency
  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    if (typeof amount === 'string' && amount.includes('$')) return amount;
    return `$${amount}`;
  };

  // Helper function to format percentage
  const formatPercentage = (percentage) => {
    if (!percentage) return 'N/A';
    if (typeof percentage === 'string' && percentage.includes('%')) return percentage;
    return `${percentage}%`;
  };

  // Calculate derived values
  const investmentAmount = investors.investment_amount || 'N/A';
  const valuation = investors.valuation || 'N/A';
  const equityPercentage = deal.equity_percentage || 'N/A';
  

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-zinc-900 mb-2">
            {company.company_name || 'Company Name'} - {company.stage || 'Series'} Term Sheet
          </h1>
          <div className="flex justify-center gap-4 mt-4">
            <Badge variant="outline" className="flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              {company.industry || 'Industry'}
            </Badge>
            <Badge variant="outline" className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              {formatCurrency(investmentAmount)}
            </Badge>
            <Badge variant="outline" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              {investors.lead_investor || 'Investor'}
            </Badge>
          </div>
        </div>

        <Separator className="mb-8" />

        {/* Term Sheet Content */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Term Sheet Document
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-900 font-mono bg-zinc-50 p-4 rounded-lg overflow-x-auto">
                {generatedTermSheet || 'Generating term sheet...'}
              </pre>
            </div>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Building2 className="w-4 h-4" />
                Company Details
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1 text-sm">
                <div><span className="font-medium">Name:</span> {company.company_name || 'N/A'}</div>
                <div><span className="font-medium">Industry:</span> {company.industry || 'N/A'}</div>
                <div><span className="font-medium">Stage:</span> {company.stage || 'N/A'}</div>
                <div><span className="font-medium">Revenue:</span> {company.revenue || 'N/A'}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Investment Details
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1 text-sm">
                <div><span className="font-medium">Amount:</span> {formatCurrency(investmentAmount)}</div>
                <div><span className="font-medium">Valuation:</span> {formatCurrency(valuation)}</div>
                <div><span className="font-medium">Equity:</span> {formatPercentage(equityPercentage)}</div>
                <div><span className="font-medium">Investor:</span> {investors.lead_investor || 'N/A'}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Key Terms
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1 text-sm">
                <div><span className="font-medium">Liquidation:</span> {deal.liquidation_preference || 'N/A'}</div>
                <div><span className="font-medium">Anti-dilution:</span> {deal.anti_dilution || 'N/A'}</div>
                <div><span className="font-medium">Board:</span> {deal.board_seats || 'N/A'}</div>
                <div><span className="font-medium">Exclusivity:</span> {terms.exclusivity_period || 'N/A'}</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 mt-8">
          <Button 
            variant="outline" 
            onClick={() => onEdit && onEdit()}
            className="flex items-center gap-2"
          >
            <Edit className="w-4 h-4" />
            Edit Information
          </Button>
          <Button 
            className="bg-indigo-600 hover:bg-indigo-700 flex items-center gap-2"
            onClick={() => {
              if (!generatedTermSheet) return;
              // Create a downloadable version
              const blob = new Blob([generatedTermSheet], { type: 'text/markdown' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${company.company_name || 'TermSheet'}_TermSheet.md`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
            }}
            disabled={!generatedTermSheet}
          >
            <Download className="w-4 h-4" />
            Download Term Sheet
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DynamicTermSheet;
