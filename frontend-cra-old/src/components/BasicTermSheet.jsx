import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { Button } from "./ui/button";
import { Building2, DollarSign, FileText, Edit, Download } from "lucide-react";

const BasicTermSheet = ({ termSheetData, onEdit }) => {
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

  const { company, investors, deal, terms } = termSheetData;

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-zinc-900 mb-2">Term Sheet</h1>
          <p className="text-zinc-600">{company.company_name || 'Company Name'}</p>
          <Badge variant="outline" className="mt-2">
            {company.stage || 'Funding Stage'}
          </Badge>
        </div>

        <Separator className="mb-8" />

        {/* Company Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              Company Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-zinc-600">Company Name</label>
                <p className="text-zinc-900">{company.company_name || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600">Industry</label>
                <p className="text-zinc-900">{company.industry || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600">Stage</label>
                <p className="text-zinc-900">{company.stage || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600">Revenue</label>
                <p className="text-zinc-900">{company.revenue || 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Investment Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Investment Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-zinc-600">Lead Investor</label>
                <p className="text-zinc-900">{investors.lead_investor || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600">Investment Amount</label>
                <p className="text-zinc-900">{investors.investment_amount || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600">Pre-money Valuation</label>
                <p className="text-zinc-900">{investors.valuation || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600">Equity Percentage</label>
                <p className="text-zinc-900">{deal.equity_percentage || 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Terms */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Key Terms
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-zinc-600">Liquidation Preference</label>
                  <p className="text-zinc-900">{deal.liquidation_preference || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-600">Board Composition</label>
                  <p className="text-zinc-900">{deal.board_seats || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-600">Anti-dilution Protection</label>
                  <p className="text-zinc-900">{deal.anti_dilution || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-600">Exclusivity Period</label>
                  <p className="text-zinc-900">{terms.exclusivity_period || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-600">Founder Vesting</label>
                  <p className="text-zinc-900">{terms.vesting_schedule || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-600">Drag-along Rights</label>
                  <p className="text-zinc-900">{terms.drag_along || 'N/A'}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 mt-8">
          <Button 
            variant="outline" 
            onClick={() => onEdit && onEdit()}
            className="flex items-center gap-2"
          >
            <Edit className="w-4 h-4" />
            Edit Terms
          </Button>
          <Button 
            className="bg-indigo-600 hover:bg-indigo-700 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download PDF
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BasicTermSheet;
