import React, { useState } from 'react';
import { Button } from './ui/Button';
import { Textarea } from './ui/Textarea';
import { TermSheetEditor } from './TermSheetEditor';
import { generateTermSheet } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { Loader2, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';

interface TermSheetGeneratorProps {
  onTermSheetGenerated?: (termSheet: string, dealConfig: Record<string, any>) => void;
}

export const TermSheetGenerator: React.FC<TermSheetGeneratorProps> = ({ onTermSheetGenerated }) => {
  const [nlInput, setNlInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [termSheet, setTermSheet] = useState<string | null>(null);
  const [dealConfig, setDealConfig] = useState<Record<string, any> | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [clarificationQuestions, setClarificationQuestions] = useState<string[] | null>(null);
  const { showError, showSuccess, showWarning } = useToast();

  const handleGenerate = async () => {
    if (!nlInput.trim()) {
      showError('Input required', 'Please enter a natural language description of the deal terms.');
      return;
    }

    console.log('[TermSheetGenerator] Starting generation with input:', nlInput.trim());
    setIsGenerating(true);
    setTermSheet(null);
    setDealConfig(null);
    setValidationErrors([]);
    setClarificationQuestions(null);

    try {
      console.log('[TermSheetGenerator] Calling API...');
      const result = await generateTermSheet(nlInput.trim());
      console.log('[TermSheetGenerator] API response received:', { 
        hasTermSheet: !!result.term_sheet,
        hasErrors: !!(result.validation_errors && result.validation_errors.length > 0)
      });
      
      setTermSheet(result.term_sheet);
      setDealConfig(result.deal_config);
      setValidationErrors(result.validation_errors || []);
      setClarificationQuestions(result.clarification_questions || null);

      if (result.term_sheet) {
        showSuccess('Term sheet generated', 'Your term sheet has been generated successfully.');
        
        if (onTermSheetGenerated) {
          onTermSheetGenerated(result.term_sheet, result.deal_config);
        }
      }

      if (result.validation_errors && result.validation_errors.length > 0) {
        showWarning('Validation warnings', `Generated with ${result.validation_errors.length} warning(s).`);
      }
    } catch (error: any) {
      console.error('[TermSheetGenerator] Error generating term sheet:', error);
      showError('Generation failed', error?.message || 'Failed to generate term sheet. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setNlInput('');
    setTermSheet(null);
    setDealConfig(null);
    setValidationErrors([]);
    setClarificationQuestions(null);
  };

  return (
    <div className="w-full h-full overflow-y-auto p-4 space-y-4 min-h-0 relative">
      {isGenerating && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl p-6 flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            <div className="text-lg font-semibold text-gray-900">Generating Term Sheet...</div>
            <div className="text-sm text-gray-600">This may take a few moments</div>
          </div>
        </div>
      )}
      <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
        <div className="flex items-center gap-3 mb-4">
          <FileText className="w-6 h-6 text-indigo-600" />
          <h2 className="text-2xl font-bold text-gray-900">Term Sheet Generator</h2>
        </div>
        
        <p className="text-gray-600 text-sm">
          Describe your deal terms in natural language. For example: "5M at 25 premoney, 1 board seat"
        </p>

        <div className="space-y-3">
          <Textarea
            value={nlInput}
            onChange={(e) => setNlInput(e.target.value)}
            placeholder="e.g., 5M at 25 premoney, 1 board seat, 15% option pool pre-money"
            rows={4}
            className="w-full resize-none"
            disabled={isGenerating}
          />

          <div className="flex gap-3 items-center">
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !nlInput.trim()}
              className="flex items-center gap-2 min-w-[160px]"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  Generate Term Sheet
                </>
              )}
            </Button>
            {termSheet && (
              <Button
                onClick={handleReset}
                variant="outline"
                disabled={isGenerating}
              >
                Reset
              </Button>
            )}
            {isGenerating && (
              <div className="text-sm text-gray-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing your request...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">Validation Warnings</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
                {validationErrors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Clarification Questions */}
      {clarificationQuestions && clarificationQuestions.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-2">Clarification Needed</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
                {clarificationQuestions.map((question, idx) => (
                  <li key={idx}>{question}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Generated Term Sheet */}
      {termSheet && (
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
              <h3 className="text-xl font-bold text-gray-900">Generated Term Sheet</h3>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => {
                  // Get HTML content from editor
                  const editorElement = document.querySelector('.term-sheet-editor .ProseMirror');
                  const contentToCopy = editorElement ? editorElement.innerHTML : termSheet;
                  navigator.clipboard.writeText(contentToCopy);
                  showSuccess('Copied', 'Term sheet HTML copied to clipboard.');
                }}
                variant="outline"
                size="sm"
              >
                Copy HTML
              </Button>
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(termSheet);
                  showSuccess('Copied', 'Term sheet markdown copied to clipboard.');
                }}
                variant="outline"
                size="sm"
              >
                Copy Markdown
              </Button>
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg bg-gray-50 max-h-[800px] overflow-y-auto">
            <TermSheetEditor 
              content={termSheet} 
              editable={true}
              onChange={(newContent) => {
                // Save edited content
                setTermSheet(newContent);
              }}
            />
          </div>
        </div>
      )}

      {/* Deal Config Summary (Collapsible) */}
      {dealConfig && (
        <details className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <summary className="cursor-pointer font-semibold text-gray-700 mb-2">
            Deal Configuration (Click to expand)
          </summary>
          <pre className="text-xs text-gray-600 overflow-x-auto mt-2">
            {JSON.stringify(dealConfig, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

export default TermSheetGenerator;
