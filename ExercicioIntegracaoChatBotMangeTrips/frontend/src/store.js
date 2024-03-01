// src/store.js
import { createStore } from 'vuex';

export default createStore({
 state: {
    minhaVariavel: null
 },
 mutations: {
    setMinhaVariavel(state, value) {
      state.minhaVariavel = value;
    }
 },
 actions: {
    updateMinhaVariavel({ commit }, value) {
      commit('setMinhaVariavel', value);
    }
 }
});