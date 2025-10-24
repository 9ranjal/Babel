import React, { useState } from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { CheckCircle, Circle, Edit, X, AlertCircle, Info } from 'lucide-react';

const ChipItem = ({
  chip,
  onUpdate,
  onRemove,
  isEditable = true,
  showSuggestions = false
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(chip.value || '');

  const handleSave = () => {
    onUpdate(chip.id, editValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(chip.value || '');
    setIsEditing(false);
  };

  const getStatusIcon = () => {
    switch (chip.status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'required':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'optional':
        return <Circle className="w-4 h-4 text-gray-400" />;
      default:
        return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (chip.status) {
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'required':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'optional':
        return 'bg-gray-50 border-gray-200 text-gray-600';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const renderInput = () => {
    if (!isEditing) {
      return (
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{chip.label}</span>
          {chip.value && (
            <Badge variant="outline" className="text-xs">
              {chip.value}
            </Badge>
          )}
        </div>
      );
    }

    switch (chip.type) {
      case 'text':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">{chip.label}</label>
            <Input
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder={chip.placeholder}
              className="w-full"
            />
          </div>
        );

      case 'number':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">{chip.label}</label>
            <Input
              type="number"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder={chip.placeholder}
              className="w-full"
            />
          </div>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">{chip.label}</label>
            <Select value={editValue} onValueChange={setEditValue}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select an option" />
              </SelectTrigger>
              <SelectContent>
                {chip.options?.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        );

      case 'boolean':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">{chip.label}</label>
            <div className="flex gap-4">
              <Button
                variant={editValue === 'true' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setEditValue('true')}
              >
                Yes
              </Button>
              <Button
                variant={editValue === 'false' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setEditValue('false')}
              >
                No
              </Button>
            </div>
          </div>
        );

      case 'date':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">{chip.label}</label>
            <Input
              type="date"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full"
            />
          </div>
        );

      default:
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">{chip.label}</label>
            <Textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder={chip.placeholder}
              className="w-full"
              rows={3}
            />
          </div>
        );
    }
  };

  return (
    <Card className={`transition-all duration-200 ${getStatusColor()}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {getStatusIcon()}
            <div className="flex-1">
              {renderInput()}
              {chip.description && (
                <p className="text-xs text-gray-600 mt-1 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  {chip.description}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={!editValue && chip.validation?.required}
                >
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCancel}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                {isEditable && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setIsEditing(true)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                )}
                {onRemove && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onRemove(chip.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChipItem;
