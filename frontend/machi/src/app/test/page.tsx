'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePet } from '@/contexts/PetContext';
import { useAuth } from '@/contexts/AuthContext';
import { petApi } from '@/libs/api/petApi';
import type { PetState } from '@/types/pet.types';

export default function APITestPage() {
  const [petName, setPetName] = useState('Mochi');
  const [petSpecies, setPetSpecies] = useState('cat');
  const [selectedPetId, setSelectedPetId] = useState('');
  const [petStateDisplay, setPetStateDisplay] = useState<PetState | null>(null);
  const [stateLoading, setStateLoading] = useState(false);

  const { user, isAuthenticated } = useAuth();
  const {
    pets,
    currentPet,
    isLoading,
    error,
    createPet,
    updatePet,
    deletePet,
    selectPetById,
  } = usePet();

  const handleCreatePet = async () => {
    try {
      const newPet = await createPet({
        name: petName,
        species: petSpecies,
      });
      alert(`Pet created! ID: ${newPet.id}`);
      setSelectedPetId(newPet.id);
    } catch (err) {
      alert(`Failed to create pet: ${err}`);
    }
  };

  const handleFetchPetState = async (petId: string) => {
    try {
      setStateLoading(true);
      const state = await petApi.getState(petId);
      setPetStateDisplay(state);
    } catch (err) {
      alert(`Failed to fetch pet state: ${err}`);
    } finally {
      setStateLoading(false);
    }
  };

  const handleUpdatePet = async (petId: string) => {
    try {
      await updatePet(petId, {
        name: `${petName} (Updated)`,
      });
      alert('Pet updated!');
    } catch (err) {
      alert(`Failed to update pet: ${err}`);
    }
  };

  const handleDeletePet = async (petId: string) => {
    if (!confirm('Are you sure you want to delete this pet?')) return;
    try {
      await deletePet(petId);
      alert('Pet deleted!');
      setSelectedPetId('');
      setPetStateDisplay(null);
    } catch (err) {
      alert(`Failed to delete pet: ${err}`);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">Pet Context Test Dashboard</h1>
        <p className="text-muted-foreground">Test PetContext functionality</p>
      </div>

      {/* Auth Status */}
      <Card>
        <CardHeader>
          <CardTitle>Authentication Status</CardTitle>
        </CardHeader>
        <CardContent>
          {isAuthenticated && user ? (
            <div className="space-y-2">
              <p className="text-sm">✅ Authenticated as: <strong>{user.email}</strong></p>
              <p className="text-sm">User ID: {user.id}</p>
              <p className="text-sm">Display Name: {user.display_name}</p>
            </div>
          ) : (
            <p className="text-sm text-yellow-600">⚠️ Not authenticated. Please login first at <a href="/auth" className="underline">/auth</a></p>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-500">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-600">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Current Pet Display */}
      {currentPet && (
        <Card className="border-blue-500">
          <CardHeader>
            <CardTitle>Current Pet</CardTitle>
            <CardDescription>The pet currently selected in context</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p><strong>ID:</strong> {currentPet.id}</p>
              <p><strong>Name:</strong> {currentPet.name}</p>
              <p><strong>Species:</strong> {currentPet.species}</p>
              <p><strong>Description:</strong> {currentPet.description || 'None'}</p>
              <p><strong>Level:</strong> {currentPet.state_json.level}</p>
              <p><strong>XP:</strong> {currentPet.state_json.xp} / {currentPet.state_json.xp_to_next_level}</p>
              <p><strong>Energy:</strong> {currentPet.state_json.energy}%</p>
              <p><strong>Hunger:</strong> {currentPet.state_json.hunger}%</p>
              <p><strong>Happiness:</strong> {currentPet.state_json.happiness}%</p>
              <p><strong>Health:</strong> {currentPet.state_json.health}%</p>
              <p><strong>Mood:</strong> {currentPet.state_json.mood}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Pets List */}
      <Card>
        <CardHeader>
          <CardTitle>All Pets ({pets.length})</CardTitle>
          <CardDescription>Pets automatically loaded when authenticated</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <p className="text-sm text-muted-foreground">Loading pets...</p>
          )}
          {!isLoading && pets.length === 0 ? (
            <p className="text-sm text-muted-foreground">No pets found. Create one below!</p>
          ) : (
            <div className="space-y-2">
              {pets.map((pet) => (
                <div
                  key={pet.id}
                  className={`p-3 border rounded-md ${
                    currentPet?.id === pet.id ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{pet.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {pet.species} • Level {pet.state_json.level} • {pet.state_json.mood}
                      </p>
                    </div>
                    <Button
                      onClick={() => {
                        selectPetById(pet.id);
                        setSelectedPetId(pet.id);
                      }}
                      size="sm"
                      variant={currentPet?.id === pet.id ? 'default' : 'outline'}
                    >
                      {currentPet?.id === pet.id ? 'Selected' : 'Select'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Pet */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Pet</CardTitle>
          <CardDescription>Add a new pet using PetContext</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Pet Name</Label>
            <Input
              type="text"
              value={petName}
              onChange={(e) => setPetName(e.target.value)}
              placeholder="Enter pet name"
            />
          </div>
          <div className="space-y-2">
            <Label>Species</Label>
            <Input
              type="text"
              value={petSpecies}
              onChange={(e) => setPetSpecies(e.target.value)}
              placeholder="cat, dog, dragon, etc."
            />
          </div>
          <Button
            onClick={handleCreatePet}
            disabled={isLoading || !isAuthenticated}
            className="w-full"
          >
            {isLoading ? 'Creating...' : 'Create Pet'}
          </Button>
        </CardContent>
      </Card>

      {/* Pet Operations */}
      {selectedPetId && (
        <Card>
          <CardHeader>
            <CardTitle>Pet Operations</CardTitle>
            <CardDescription>Actions for pet: {selectedPetId.slice(0, 8)}...</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              onClick={() => handleFetchPetState(selectedPetId)}
              disabled={stateLoading}
              variant="outline"
              className="w-full"
            >
              {stateLoading ? 'Loading...' : 'Fetch Pet State (Cached)'}
            </Button>
            <Button
              onClick={() => handleUpdatePet(selectedPetId)}
              disabled={isLoading}
              variant="outline"
              className="w-full"
            >
              Update Pet Name
            </Button>
            <Button
              onClick={() => handleDeletePet(selectedPetId)}
              disabled={isLoading}
              variant="destructive"
              className="w-full"
            >
              Delete Pet
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Pet State Display */}
      {petStateDisplay && (
        <Card>
          <CardHeader>
            <CardTitle>Pet State (Detailed)</CardTitle>
            <CardDescription>Full state from /state endpoint</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-md overflow-auto max-h-96 text-xs">
              {JSON.stringify(petStateDisplay, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Context State */}
      <Card>
        <CardHeader>
          <CardTitle>PetContext State</CardTitle>
          <CardDescription>Current state of PetContext</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded-md overflow-auto max-h-96 text-xs">
            {JSON.stringify(
              {
                petsCount: pets.length,
                currentPetId: currentPet?.id,
                isLoading,
                error,
              },
              null,
              2
            )}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
