import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Building2, 
  DollarSign, 
  Users, 
  Shield, 
  Lock, 
  Clock, 
  FileText,
  Play,
  CheckCircle
} from 'lucide-react';
import ChipCollection from './ChipCollection';
import DynamicTermSheet from '../DynamicTermSheet';
import { InformationState } from './types';

export const ChipSystemDemo: React.FC = () => {
  const [currentView, setCurrentView] = useState<'chips' | 'term-sheet'>('chips');
  const [informationState, setInformationState] = useState<InformationState | null>(null);
  const [termSheetData, setTermSheetData] = useState<any>(null);

  const handleInformationUpdate = (state: InformationState) => {
    setInformationState(state);
  };

  const handleTermSheetReady = (data: any) => {
    setTermSheetData(data);
    setCurrentView('term-sheet');
  };

  const getOverallProgress = () => {
    if (!informationState) return 0;
    const allChips = informationState.chips;
    const completedChips = allChips.filter(chip => chip.value && chip.value !== '');
    return allChips.length > 0 ? (completedChips.length / allChips.length) * 100 : 0;
  };

  const getCompletedCategories = () => {
    if (!informationState) return 0;
    return informationState.completedCategories.length;
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Chip-Based Term Sheet Collection</h1>
            <p className="text-gray-600">Interactive information collection using contextual chips</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-gray-600">Progress</div>
              <div className="text-lg font-semibold">{Math.round(getOverallProgress())}%</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Categories</div>
              <div className="text-lg font-semibold">{getCompletedCategories()}/7</div>
            </div>
            {informationState?.canGenerateTermSheet && (
              <Badge className="bg-green-100 text-green-800 border-green-200">
                <CheckCircle className="w-4 h-4 mr-1" />
                Ready for Term Sheet
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <Tabs value={currentView} onValueChange={(value) => setCurrentView(value as 'chips' | 'term-sheet')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="chips" className="flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              Information Collection
            </TabsTrigger>
            <TabsTrigger 
              value="term-sheet" 
              className="flex items-center gap-2"
              disabled={!informationState?.canGenerateTermSheet}
            >
              <FileText className="w-4 h-4" />
              Generated Term Sheet
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={currentView} className="h-full">
          <TabsContent value="chips" className="h-full m-0">
            <ChipCollection
              onInformationUpdate={handleInformationUpdate}
              onTermSheetReady={handleTermSheetReady}
            />
          </TabsContent>
          
          <TabsContent value="term-sheet" className="h-full m-0">
            {termSheetData ? (
              <DynamicTermSheet
                termSheetData={termSheetData}
                onEdit={() => setCurrentView('chips')}
              />
            ) : (
              <div className="h-full flex items-center justify-center">
                <Card className="max-w-md mx-auto">
                  <CardContent className="text-center py-8">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-semibold mb-2">No Term Sheet Generated</h3>
                    <p className="text-gray-600 mb-4">
                      Complete the information collection to generate a term sheet.
                    </p>
                    <Button 
                      onClick={() => setCurrentView('chips')}
                      className="bg-indigo-600 hover:bg-indigo-700"
                    >
                      Continue Collection
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Information State Debug (Development Only) */}
      {process.env.NODE_ENV === 'development' && informationState && (
        <div className="bg-gray-100 border-t border-gray-200 p-4">
          <details className="text-xs">
            <summary className="cursor-pointer font-medium">Debug Information</summary>
            <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto max-h-32">
              {JSON.stringify({
                completedCategories: informationState.completedCategories,
                canGenerateTermSheet: informationState.canGenerateTermSheet,
                completedChips: informationState.chips.filter(c => c.value && c.value !== '').length,
                totalChips: informationState.chips.length
              }, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default ChipSystemDemo;
