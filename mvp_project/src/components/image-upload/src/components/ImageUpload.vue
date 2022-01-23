<template>
  <div
    v-if="image"
    class="image-upload_wrapper d-flex align-center justify-content-center container-fluid"
  >
    <div class="d-flex flex-column justify-content-center">
      <Cropper
        class="upload-cropper mx-auto"
        :src="image"
        :stencilComponent="CircleStencil"
        @change="change"
      />
      <div
        class="button-wrapper d-flex flex-align-center justify-content-center my-4"
      >
        <!-- <button
          class="button btn btn-light border-secondary mx-4"
          @click="rotateImage"
        >
          {{ rotateText }}
        </button> -->

        <button
          class="button btn btn-light border-secondary mx-4"
          @click="save"
        >
          {{ saveText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { Cropper } from "vue-advanced-cropper";
import CircleStencil from "./CircleStencil";

export default {
  name: "UploadImage",
  data() {
    return {
      image: null,
      canvas: null,
      uploadText: "",
      rotateText: "",
      saveText: ""
    };
  },
  components: {
    Cropper
  },
  computed: {
    CircleStencil() {
      return CircleStencil;
    },
    avatarElement() {
      return document.querySelector(".avatar");
    }
  },
  methods: {
    rotateImage() {
      var image = document.createElement("img");
      image.crossOrigin = "anonymous";
      image.src = this.image;
      image.onload = () => {
        var canvas = document.createElement("canvas");
        var ctx = canvas.getContext("2d");

        if (image.width > image.height) {
          canvas.width = image.height;
          canvas.height = image.width;
          ctx.translate(image.height, image.width / image.height);
        } else {
          canvas.height = image.width;
          canvas.width = image.height;
          ctx.translate(image.height, image.width / image.height);
        }
        ctx.rotate(Math.PI / 2);
        ctx.drawImage(image, 0, 0);
        this.image = canvas.toDataURL();
      };
    },
    uploadImage(event) {
      // Reference to the DOM input element
      var input = event.target;
      // Ensure that you have a file before attempting to read it
      if (input.files && input.files[0]) {
        // create a new FileReader to read this image and convert to base64 format
        var reader = new FileReader();
        // Define a callback function to run, when FileReader finishes its job
        reader.onload = e => {
          // Note: arrow function used here, so that "this.imageData" refers to the imageData of Vue component
          // Read image as base64 and set to imageData
          this.image = e.target.result;
        };
        // Start the reader job - read file as a data url (base64 format)
        reader.readAsDataURL(input.files[0]);
      }
    },
    change({ canvas }) {
      this.canvas = canvas;
    },
    save(event) {
      this.avatarElement.style.backgroundImage = `url(${this.canvas.toDataURL()})`;
      this.image = null;

      const mimeType = "image/*";

      function getCookie(name) {
        let matches = document.cookie.match(
          new RegExp(
            "(?:^|; )" +
              name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, "\\$1") +
              "=([^;]*)"
          )
        );
        return matches ? decodeURIComponent(matches[1]) : undefined;
      }

      const token = getCookie("csrftoken");

      axios({
        url: "/api/v1/image/",
        method: "put",
        data: { image: this.canvas.toDataURL() },
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": token
        }
      })
      .then(response => {
        if (response.status === 200) {
          // location.reload();
          const noPhotoMessage = document.getElementById("no-photo")
          noPhotoMessage.hidden = true
        }
      })
    }
  },
  created() {
    const attrs = document.querySelector("#app").attributes;

    this.saveText = attrs.savetext.value;
    this.rotateText = attrs.rotatetext.value;

    const inputElement = document.querySelector(
      '.profile-form input[type="file"]'
    );

    inputElement.onchange = event => this.uploadImage(event);
  }
};
</script>

<style lang="scss" scoped>
.image-upload_wrapper * {
  max-width: 100%;
}

.image-upload_wrapper {
  background: black;
  width: 100%;
  max-width: 100%;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  overflow: hidden;
}

.upload-cropper {
  height: 80vh;
  width: 40rem;
  max-width: 100%;
}

.button-wrapper {
  padding-bottom: 3.5rem;
}

.button {
  cursor: pointer;
  transition: background 0.5s;
  font-family: Open Sans, Arial;
}

.button input {
  display: none;
}

.upload-cropper.vue-advanced-cropper {
  margin: auto;
}
</style>
