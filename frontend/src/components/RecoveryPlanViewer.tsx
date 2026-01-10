"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, CheckCircle, AlertCircle, Clock, Pill, Heart, AlertTriangle } from 'lucide-react';

interface RecoveryPlan {
  id: string;
  date: string;
  diagnosis: string;
  recovery_plan: {
    title: string;
    subtitle: string;
    daily_plans: Array<{
      day: string;
      tasks: Array<{
        task: string;
        completed: boolean;
      }>;
      medications_to_take: string[];
    }>;
    healthy_habits: string[];
    important_restrictions: string[];
    emergency_signs: string[];
  };
  uploaded_at: string;
  filename: string;
}

export default function RecoveryPlansPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<RecoveryPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<RecoveryPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRecoveryPlans();
  }, []);

  const fetchRecoveryPlans = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch('/api/recovery-plans', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data.recovery_plans || []);
        if (data.recovery_plans && data.recovery_plans.length > 0) {
          setSelectedPlan(data.recovery_plans[0]);
        }
      } else {
        setError('Failed to load recovery plans');
      }
    } catch (err) {
      console.error('Error fetching recovery plans:', err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleTask = (planId: string, dayIndex: number, taskIndex: number) => {
    setPlans(prevPlans => 
      prevPlans.map(plan => {
        if (plan.id === planId) {
          const updatedPlan = { ...plan };
          updatedPlan.recovery_plan.daily_plans[dayIndex].tasks[taskIndex].completed = 
            !updatedPlan.recovery_plan.daily_plans[dayIndex].tasks[taskIndex].completed;
          return updatedPlan;
        }
        return plan;
      })
    );
    
    if (selectedPlan?.id === planId) {
      setSelectedPlan(prev => {
        if (!prev) return null;
        const updated = { ...prev };
        updated.recovery_plan.daily_plans[dayIndex].tasks[taskIndex].completed = 
          !updated.recovery_plan.daily_plans[dayIndex].tasks[taskIndex].completed;
        return updated;
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-20">
            <div className="animate-pulse">
              <Calendar className="h-16 w-16 mx-auto text-purple-600 mb-4" />
              <p className="text-stone-600">Loading your recovery plans...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-20">
            <AlertCircle className="h-16 w-16 mx-auto text-red-500 mb-4" />
            <p className="text-red-600 text-lg">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-purple-900 mb-6">📋 My Recovery Plans</h1>
          <div className="text-center py-20 bg-white rounded-lg shadow-md">
            <Calendar className="h-16 w-16 mx-auto text-stone-400 mb-4" />
            <p className="text-stone-600 text-lg mb-2">No recovery plans yet</p>
            <p className="text-stone-500 text-sm">Upload a discharge summary to generate your recovery plan</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-purple-900 mb-6 flex items-center gap-3">
          📋 My Recovery Plans
        </h1>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Plans List Sidebar */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-sm font-semibold text-stone-600 uppercase mb-3">Your Plans</h2>
            {plans.map((plan) => (
              <button
                key={plan.id}
                onClick={() => setSelectedPlan(plan)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  selectedPlan?.id === plan.id
                    ? 'border-purple-600 bg-purple-50 shadow-md'
                    : 'border-stone-200 bg-white hover:border-purple-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-4 w-4 text-purple-600" />
                  <span className="text-xs text-stone-500">
                    {new Date(plan.date).toLocaleDateString()}
                  </span>
                </div>
                <p className="font-medium text-stone-900 text-sm line-clamp-2">
                  {plan.diagnosis}
                </p>
              </button>
            ))}
          </div>

          {/* Selected Plan Details */}
          {selectedPlan && (
            <div className="lg:col-span-3 space-y-6">
              {/* Header */}
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg p-6 shadow-lg">
                <h2 className="text-2xl font-bold mb-2">{selectedPlan.recovery_plan.title}</h2>
                <p className="text-purple-100">{selectedPlan.recovery_plan.subtitle}</p>
                <div className="mt-4 flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {new Date(selectedPlan.date).toLocaleDateString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Heart className="h-4 w-4" />
                    {selectedPlan.diagnosis}
                  </span>
                </div>
              </div>

              {/* Daily Plans */}
              <div className="space-y-4">
                {selectedPlan.recovery_plan.daily_plans.map((day, dayIndex) => (
                  <div key={dayIndex} className="bg-white rounded-lg p-6 shadow-md border border-stone-200">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-full bg-purple-600 text-white flex items-center justify-center text-lg font-bold">
                        {dayIndex + 1}
                      </div>
                      <h3 className="font-bold text-xl text-purple-900">{day.day}</h3>
                    </div>

                    {/* Tasks */}
                    <div className="space-y-2 mb-4">
                      {day.tasks.map((task, taskIndex) => (
                        <label
                          key={taskIndex}
                          className="flex items-start gap-3 p-3 rounded-lg hover:bg-stone-50 cursor-pointer transition-colors"
                        >
                          <input
                            type="checkbox"
                            checked={task.completed}
                            onChange={() => toggleTask(selectedPlan.id, dayIndex, taskIndex)}
                            className="mt-1 h-5 w-5 text-purple-600 rounded border-stone-300 focus:ring-purple-500"
                          />
                          <span className={`flex-1 ${task.completed ? 'line-through text-stone-400' : 'text-stone-700'}`}>
                            {task.task}
                          </span>
                          {task.completed && (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          )}
                        </label>
                      ))}
                    </div>

                    {/* Medications */}
                    {day.medications_to_take && day.medications_to_take.length > 0 && (
                      <div className="pt-4 border-t border-stone-200">
                        <div className="flex items-center gap-2 mb-3">
                          <Pill className="h-5 w-5 text-purple-600" />
                          <span className="font-semibold text-purple-900">Medications to Take</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {day.medications_to_take.map((med, medIdx) => (
                            <span
                              key={medIdx}
                              className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium"
                            >
                              💊 {med}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Healthy Habits & Restrictions */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Healthy Habits */}
                {selectedPlan.recovery_plan.healthy_habits && selectedPlan.recovery_plan.healthy_habits.length > 0 && (
                  <div className="bg-green-50 rounded-lg p-6 border-2 border-green-200">
                    <h4 className="font-bold text-green-900 mb-4 flex items-center gap-2 text-lg">
                      <Heart className="h-5 w-5" />
                      Healthy Habits
                    </h4>
                    <ul className="space-y-3">
                      {selectedPlan.recovery_plan.healthy_habits.map((habit, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-green-800">
                          <CheckCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                          <span>{habit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Important Restrictions */}
                {selectedPlan.recovery_plan.important_restrictions && selectedPlan.recovery_plan.important_restrictions.length > 0 && (
                  <div className="bg-orange-50 rounded-lg p-6 border-2 border-orange-200">
                    <h4 className="font-bold text-orange-900 mb-4 flex items-center gap-2 text-lg">
                      <AlertTriangle className="h-5 w-5" />
                      Important Restrictions
                    </h4>
                    <ul className="space-y-3">
                      {selectedPlan.recovery_plan.important_restrictions.map((restriction, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-orange-800">
                          <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                          <span>{restriction}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Emergency Signs */}
              {selectedPlan.recovery_plan.emergency_signs && selectedPlan.recovery_plan.emergency_signs.length > 0 && (
                <div className="bg-red-50 rounded-lg p-6 border-2 border-red-200">
                  <h4 className="font-bold text-red-900 mb-4 flex items-center gap-2 text-lg">
                    🚨 Seek Medical Help If You Experience:
                  </h4>
                  <ul className="space-y-3">
                    {selectedPlan.recovery_plan.emergency_signs.map((sign, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-red-800">
                        <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                        <span>{sign}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
