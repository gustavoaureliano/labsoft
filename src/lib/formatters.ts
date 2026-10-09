const formatter = {
 Minutes(minCount): string{
    if(minCount>=60){
      return String(Math.trunc(minCount/60)) + "h " + String(minCount%60) + "min"; 
    } else {
      return String(minCount%60) + "min"; 
    }
  },


  Stars(rating): string {
    const value = String(rating.toFixed(2));
    if(rating == 0){
      return "☆☆☆☆☆ " + value;
    } else if(0 < rating && rating < 1){
      return "⯪☆☆☆☆ " + value;
    } else if(rating == 1){
      return "★☆☆☆☆ " + value;
    } else if(1 < rating && rating < 2){
      return "★⯪☆☆☆ " + value;
    } else if(rating == 2){
      return "★★☆☆☆ " + value;
    } else if(2 < rating && rating < 3){
      return "★★⯪☆☆ " + value;
    } else if(rating == 3){
      return "★★★☆☆ " + value;
    } else if(3 < rating && rating < 4){
      return "★★★⯪☆ " + value;
    } else if(rating == 4){
      return "★★★★☆ " + value;
    } else if(4 < rating && rating < 5){
      return "★★★★⯪ " + value;
    } else if(rating == 5){
      return "★★★★★ " + value;
    } else {
      return "nda";

    }
  }
};

export default formatter;
