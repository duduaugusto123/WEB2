<script setup>
    const id = ref(0)
    const { data: conversationHistory } = await useFetch('http://localhost:8000/conversationhistory/?historyId=1')
    const { data: conversation } = await useFetch(`http://localhost:8000/conversation/`)    
    console.log(conversationHistory)
    console.log(conversation)
    var idsHistory = []
    for(let x in conversationHistory.value.results){
        idsHistory.push(parseInt(conversationHistory.value.results[x].id)) 
        console.log(idsHistory)
    }
    console.log(conversation.value.results[0].type == 'Q')
</script>

<template>
    <!-- // (idsHistory[index] == conversation.results[index].history.id) -->
    <div>
        <div class="conteinerSideBar" v-for="(conv, index) in (conversation.results.length-1)" :key="index">

            
            <p v-if="conversation.results[index].type == 'Q' && conversation.results[index].history.id in idsHistory">
                {{conversation.results[index].message}}
            </p>
        </div>
    </div>
</template>