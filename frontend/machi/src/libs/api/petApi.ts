import axiosInstance from "@/libs/axios";

import type { Pet, PetState, PetCreate, PetUpdate } from '@/types/pet.types';



export const petApi = {
    async getAll(): Promise<Pet[]> {
        const { data } = await axiosInstance.get<Pet[]>('/api/v1/pets');
        return data;
    },

    async getById(petId: string): Promise<Pet> {
        const { data } = await axiosInstance.get<Pet>(`/api/v1/pets/${petId}`);
        return data;
    },

    async getState(petId: string): Promise<PetState> {
        const { data } = await axiosInstance.get<PetState>(`/api/v1/pets/${petId}/state`);
        return data;
    },

    async create(petData: PetCreate): Promise<Pet> {
        const { data } = await axiosInstance.post<Pet>('/api/v1/pets', petData);
        return data;
    },

    async update(petId: string, petUpdate: PetUpdate): Promise<Pet> {
        const { data } = await axiosInstance.patch<Pet>(`/api/v1/pets/${petId}`, petUpdate);
        return data;
    },

    async delete(petId: string): Promise<void> {
        await axiosInstance.delete(`/api/v1/pets/${petId}`);
    },
}