import { defineStore } from "pinia";
import { fetchWrapper } from "@/helpers";

const baseUrl = `${import.meta.env.VITE_API_URL}/attributes`;

export const useAttributesStore = defineStore({
    id: "attributes",
    state: () => ({
        attributes: {},
        attribute: {},
        status: {
            loading: false,
            error: false
        }
    }),
    actions: {
        async get(params = { skip: 0, limit: 10, event_id: null }) {
            this.status = { loading: true };
            fetchWrapper
                .get(baseUrl + "/?" + new URLSearchParams(params).toString())
                .then((attributes) => (this.attributes = attributes))
                .catch((error) => (this.status = { error }))
                .finally(() => (this.status = { loading: false }));
        },
        async getById(id) {
            this.status = { loading: true };
            fetchWrapper
                .get(`${baseUrl}/${id}`)
                .then((attribute) => (this.attribute = attribute))
                .catch((error) => (this.status = { error }))
                .finally(() => (this.status = { loading: false }));
        }
    },
});
