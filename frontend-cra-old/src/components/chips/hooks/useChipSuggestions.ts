import { useState, useEffect, useCallback } from 'react';
import { ChipData, ChipSuggestion } from '../types';
import { chipCategories } from '../informationArchitecture';

export const useChipSuggestions = (completedCategories: string[], currentChips: ChipData[]) => {
  const [suggestions, setSuggestions] = useState<ChipSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Generate suggestions based on completed categories and current chips
  const generateSuggestions = useCallback(() => {
    setIsLoading(true);
    
    // Get available categories based on dependencies
    const availableCategories = chipCategories.filter(category => {
      if (!category.dependencies) return true;
      return category.dependencies.every(dep => completedCategories.includes(dep));
    });

    // Get chips from available categories that aren't already present
    const newSuggestions: ChipSuggestion[] = [];
    
    availableCategories.forEach(category => {
      if (!completedCategories.includes(category.id)) {
        // Suggest first few chips from this category
        const categoryChips = category.chips.slice(0, 3);
        categoryChips.forEach(chip => {
          if (!currentChips.find(c => c.id === chip.id)) {
            newSuggestions.push({
              chip,
              reason: `Complete ${category.name} information`,
              priority: 'high',
              basedOn: category.dependencies
            });
          }
        });
      }
    });

    // Add contextual suggestions based on current data
    const contextualSuggestions = generateContextualSuggestions(currentChips);
    newSuggestions.push(...contextualSuggestions);

    // Sort by priority
    newSuggestions.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });

    setSuggestions(newSuggestions.slice(0, 6)); // Limit to 6 suggestions
    setIsLoading(false);
  }, [completedCategories, currentChips]);

  // Generate contextual suggestions based on current chip values
  const generateContextualSuggestions = useCallback((chips: ChipData[]): ChipSuggestion[] => {
    const suggestions: ChipSuggestion[] = [];
    
    // Find company industry to suggest industry-specific terms
    const industryChip = chips.find(c => c.id === 'industry');
    if (industryChip && industryChip.value) {
      const industry = industryChip.value.toLowerCase();
      
      // Suggest industry-specific terms
      if (industry.includes('fintech')) {
        suggestions.push({
          chip: {
            id: 'regulatory_compliance',
            category: 'terms',
            label: 'Regulatory Compliance',
            value: '',
            status: 'optional',
            type: 'text',
            description: 'Regulatory compliance requirements for fintech'
          },
          reason: 'Fintech companies often need regulatory compliance terms',
          priority: 'medium',
          basedOn: ['industry']
        });
      }
      
      if (industry.includes('healthcare') || industry.includes('biotech')) {
        suggestions.push({
          chip: {
            id: 'fda_approval',
            category: 'terms',
            label: 'FDA Approval Rights',
            value: '',
            status: 'optional',
            type: 'boolean',
            description: 'Rights related to FDA approval processes'
          },
          reason: 'Healthcare companies may need FDA-related terms',
          priority: 'medium',
          basedOn: ['industry']
        });
      }
    }

    // Find investment amount to suggest appropriate terms
    const investmentChip = chips.find(c => c.id === 'investment_amount');
    if (investmentChip && investmentChip.value) {
      const amount = parseFloat(investmentChip.value);
      
      if (amount > 10000000) { // > $10M
        suggestions.push({
          chip: {
            id: 'board_observer_rights',
            category: 'terms',
            label: 'Board Observer Rights',
            value: '',
            status: 'optional',
            type: 'boolean',
            description: 'Right to observe board meetings'
          },
          reason: 'Large investments often include board observer rights',
          priority: 'medium',
          basedOn: ['investment_amount']
        });
      }
    }

    // Find security type to suggest related terms
    const securityTypeChip = chips.find(c => c.id === 'security_type');
    if (securityTypeChip && securityTypeChip.value) {
      const securityType = securityTypeChip.value.toLowerCase();
      
      if (securityType.includes('preferred')) {
        suggestions.push({
          chip: {
            id: 'dividend_rights',
            category: 'terms',
            label: 'Dividend Rights',
            value: '',
            status: 'optional',
            type: 'select',
            description: 'Dividend rights for preferred stock',
            options: ['None', 'Non-cumulative', 'Cumulative', 'Participating']
          },
          reason: 'Preferred stock often includes dividend rights',
          priority: 'medium',
          basedOn: ['security_type']
        });
      }
    }

    return suggestions;
  }, []);

  // Generate AI-powered suggestions (placeholder for Ollama integration)
  const generateAISuggestions = useCallback(async () => {
    // This would integrate with Ollama to generate contextual suggestions
    // For now, return empty array
    return [];
  }, []);

  // Update suggestions when dependencies change
  useEffect(() => {
    generateSuggestions();
  }, [generateSuggestions]);

  // Add suggestion to current chips
  const addSuggestion = useCallback((suggestion: ChipSuggestion) => {
    // This would be handled by the parent component
    // The suggestion chip would be added to the current chips
    return suggestion.chip;
  }, []);

  // Dismiss suggestion
  const dismissSuggestion = useCallback((suggestionId: string) => {
    setSuggestions(prev => prev.filter(s => s.chip.id !== suggestionId));
  }, []);

  return {
    suggestions,
    isLoading,
    generateSuggestions,
    generateAISuggestions,
    addSuggestion,
    dismissSuggestion
  };
};
