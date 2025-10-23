/**
 * Persona Intake Component
 * 
 * Conversational Q&A interface for creating company and investor personas
 * Uses the backend copilot intake API with Ollama integration
 */
import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Loader2, User, Building2, CheckCircle, ArrowRight } from 'lucide-react';
import { api } from '../lib/apiClient';

interface IntakeQuestion {
  question_id: string;
  question_text: string;
  question_type: 'choice' | 'number' | 'text' | 'boolean';
  options?: string[];
  next_questions: string[];
}

interface IntakeResponse {
  question_id: string;
  question_text: string;
  question_type: 'choice' | 'number' | 'text' | 'boolean';
  options?: string[];
  next_questions: string[];
  session_id?: string;
  persona_id?: string;
  transaction_id?: string;
}

interface PersonaIntakeProps {
  transactionId: string;
  onPersonaCreated: (personaId: string, role: 'founder' | 'investor') => void;
  onComplete: () => void;
}

export function PersonaIntake({ transactionId, onPersonaCreated, onComplete }: PersonaIntakeProps) {
  const [step, setStep] = useState<'role' | 'intake' | 'complete'>('role');
  const [role, setRole] = useState<'founder' | 'investor' | null>(null);
  const [stage, setStage] = useState('seed');
  const [region, setRegion] = useState('SG');
  const [currentQuestion, setCurrentQuestion] = useState<IntakeResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const startIntake = async () => {
    if (!role) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.post('/api/copilot/intake/start', {
        role,
        stage,
        region,
        transaction_id: transactionId
      });
      
      const questionData = response.data;
      setCurrentQuestion(questionData);
      setSessionId(questionData.session_id || null);
      setPersonaId(questionData.persona_id || null);
      setStep('intake');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to start intake');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!currentQuestion || !answer.trim()) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.post('/api/copilot/intake/answer', {
        question_id: currentQuestion.question_id,
        answer: answer.trim(),
        session_id: sessionId,
        persona_id: personaId,
        transaction_id: transactionId
      });
      
      const result = response.data;
      
      if (result.completed) {
        setCompleted(true);
        setStep('complete');
        if (result.persona_id && role) {
          onPersonaCreated(result.persona_id, role);
        }
      } else if (result.next_question) {
        setCurrentQuestion(result.next_question);
        setAnswer('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit answer');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitAnswer();
    }
  };

  const renderQuestionInput = () => {
    if (!currentQuestion) return null;

    switch (currentQuestion.question_type) {
      case 'choice':
        return (
          <div className="space-y-2">
            {currentQuestion.options?.map((option, index) => (
              <label key={index} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="answer"
                  value={option}
                  checked={answer === option}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="text-indigo-600"
                />
                <span className="text-sm">{option}</span>
              </label>
            ))}
          </div>
        );
      
      case 'boolean':
        return (
          <div className="flex gap-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="answer"
                value="true"
                checked={answer === 'true'}
                onChange={(e) => setAnswer(e.target.value)}
                className="text-indigo-600"
              />
              <span className="text-sm">Yes</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="answer"
                value="false"
                checked={answer === 'false'}
                onChange={(e) => setAnswer(e.target.value)}
                className="text-indigo-600"
              />
              <span className="text-sm">No</span>
            </label>
          </div>
        );
      
      case 'number':
        return (
          <Input
            type="number"
            placeholder="Enter a number"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyPress={handleKeyPress}
          />
        );
      
      case 'text':
      default:
        return (
          <Textarea
            placeholder="Enter your answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyPress={handleKeyPress}
            rows={3}
          />
        );
    }
  };

  if (step === 'role') {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Create Persona
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-base font-medium">What role are you creating?</Label>
            <RadioGroup value={role || ''} onValueChange={(value) => setRole(value as 'founder' | 'investor')} className="mt-3">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="founder" id="founder" />
                <Label htmlFor="founder" className="flex items-center gap-2 cursor-pointer">
                  <Building2 className="h-4 w-4" />
                  Founder/Company
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="investor" id="investor" />
                <Label htmlFor="investor" className="flex items-center gap-2 cursor-pointer">
                  <User className="h-4 w-4" />
                  Investor
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="stage">Stage</Label>
              <Select value={stage} onValueChange={setStage}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="seed">Seed</SelectItem>
                  <SelectItem value="series-a">Series A</SelectItem>
                  <SelectItem value="series-b">Series B</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="region">Region</Label>
              <Select value={region} onValueChange={setRegion}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SG">Singapore</SelectItem>
                  <SelectItem value="IN">India</SelectItem>
                  <SelectItem value="US">United States</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <Button 
            onClick={startIntake}
            disabled={!role || loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Starting intake...
              </>
            ) : (
              <>
                Start Intake
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (step === 'intake' && currentQuestion) {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            {role === 'founder' ? 'Founder' : 'Investor'} Intake
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline">{stage}</Badge>
            <Badge variant="outline">{region}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-4">{currentQuestion.question_text}</h3>
            {renderQuestionInput()}
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex gap-2">
            <Button 
              onClick={submitAnswer}
              disabled={!answer.trim() || loading}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                'Submit Answer'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (step === 'complete') {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardContent className="text-center py-8">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-600" />
          <h3 className="text-lg font-semibold mb-2">Persona Created Successfully!</h3>
          <p className="text-gray-600 mb-4">
            Your {role} persona has been created and linked to this transaction.
          </p>
          <Button onClick={onComplete} className="bg-indigo-600 hover:bg-indigo-700">
            Continue
          </Button>
        </CardContent>
      </Card>
    );
  }

  return null;
}

export default PersonaIntake;
