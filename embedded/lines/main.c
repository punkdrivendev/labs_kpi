#include <stdlib.h>
#include <stdio.h>

int str_len(char *char_arr) {
    int len = 0;

    while (char_arr[len] != '\0') {
        len++;
    }

    return len;
}

char *read_line(void) {
    size_t capacity = 16;
    size_t length = 0;

    char *str = malloc(capacity);
    if (str == NULL) {
        return NULL;
    }

    int c;

    while ((c = getchar()) != '\n' && c != EOF) {
        if (length + 1 >= capacity) {
            capacity *= 2;

            char *tmp = realloc(str, capacity);
            if (tmp == NULL) {
                free(str);
                return NULL;
            }

            str = tmp;
        }

        str[length++] = (char)c;
    }

    str[length] = '\0';

    return str;
}

void *remove_char(char *char_arr, int index) {

    int len = str_len(char_arr);
    if(index<0 || index >= len){
        return NULL;
    }
    for(int i = index; i<len; i++){
        char_arr[i] = char_arr[i+1];
    }

}

void remove_spaces(char *char_arr) {
    int size_of_arr = str_len(char_arr);

    while(char_arr[0] == ' '){
        remove_char(char_arr, 0);
        size_of_arr += -1;
    }
    while(char_arr[size_of_arr - 1] == ' '){
        remove_char(char_arr,size_of_arr-1);
        size_of_arr += -1;
    }
}

int main(){

    printf("Type away...\n");
    char *user_input = read_line();

    remove_spaces(user_input);

    printf("Result:\n|%s|", user_input);

    return 0;
}
