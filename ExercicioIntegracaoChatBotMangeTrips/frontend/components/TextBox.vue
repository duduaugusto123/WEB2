<script setup>
const props = defineProps({
    avatarImage: { type: String },
    name: { type: String },
    message: { type: String },
    type: { type: String }
})



</script>

<template>
    <div class="text-box" :class="props.type === 'right' ? 'right-style' : 'left-style'">
        <Fieldset>
            <template #legend>
                <div class="flex align-items-center pl-2">
                    <Avatar :image="props.avatarImage" shape="circle" />
                    <span class="font-bold"> {{ props.name }}</span>
                </div>
            </template>
            <p class="m-0">
                {{ props.message }}
            </p>
        </Fieldset>
    </div>
</template>

<style scoped lang="scss">

.text-box {

    .p-fieldset {
        font-size: 1rem;
        color: black;       
    }
}

.right-style {
    .p-fieldset {
        background-color: rgb(78, 78, 94);
    }
}

.left-style {
    .p-fieldset {
        background-color: rgb(69, 52, 55);
    }
}
</style>